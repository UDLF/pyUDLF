"""
Characterization tests: the wrapper must not change UDLF results.

Each test runs the same experiment twice on the synthetic dataset:
  - through pyUDLF (legacy API: InputType + run_calls.run);
  - directly with the UDLF binary, using a minimal config written by hand.
and checks that the re-ranked lists are byte-identical and the logged MAP
values match.
"""

import filecmp
from pathlib import Path

import pytest

from conftest import (METHOD_CASES, base_config, make_input, parse_map,
                      run_direct)


def _run_both(old_api, udlf_bin, udlf_template, data, tmp_path, method, params,
              **input_kwargs):
    wrap_out, wrap_log = tmp_path / "wrapper_out", tmp_path / "wrapper_log.txt"
    inp = make_input(udlf_template, data, method, params, wrap_out, wrap_log,
                     **input_kwargs)
    output = old_api.run(inp, get_output=True)

    direct_out, direct_log = tmp_path / "direct_out", tmp_path / "direct_log.txt"
    proc = run_direct(udlf_bin, base_config(data, method, params, direct_out,
                                            direct_log, **input_kwargs), tmp_path)
    assert proc.returncode == 0, proc.stdout + proc.stderr
    return output, (wrap_out, wrap_log), (direct_out, direct_log)


@pytest.mark.parametrize("method", sorted(METHOD_CASES))
def test_wrapper_matches_direct_run(old_api, udlf_bin, udlf_template, data,
                                    tmp_path, method):
    output, (wrap_out, wrap_log), (direct_out, direct_log) = _run_both(
        old_api, udlf_bin, udlf_template, data, tmp_path, method,
        METHOD_CASES[method])

    assert output, "wrapper reported a failed run"
    assert filecmp.cmp(f"{wrap_out}.txt", f"{direct_out}.txt", shallow=False)
    assert parse_map(wrap_log) == parse_map(direct_log)

    # the parsed log exposed by the wrapper agrees with the log file
    before, after = parse_map(direct_log)
    assert float(output.log_dict["MAP"]["Before"]) == pytest.approx(before)
    assert float(output.log_dict["MAP"]["After"]) == pytest.approx(after)


@pytest.mark.parametrize("variant", [
    dict(input_file="rk_str", rk_format="STR"),
    dict(input_file="matrix_dist", input_format="MATRIX", matrix_type="DIST"),
    dict(input_file="matrix_sim", input_format="MATRIX", matrix_type="SIM"),
    dict(input_file="matrix_sim", input_format="AUTO"),
], ids=["rk-str", "matrix-dist", "matrix-sim", "auto-detect-sim"])
def test_input_formats_match_direct_run(old_api, udlf_bin, udlf_template, data,
                                        tmp_path, variant):
    variant = dict(variant, input_file=data[variant["input_file"]])
    output, (wrap_out, _), (direct_out, _) = _run_both(
        old_api, udlf_bin, udlf_template, data, tmp_path, "CPRR",
        METHOD_CASES["CPRR"], **variant)

    assert output
    assert filecmp.cmp(f"{wrap_out}.txt", f"{direct_out}.txt", shallow=False)


def test_all_input_formats_agree(old_api, udlf_template, data, tmp_path):
    """Numeric RK, string RK and the distance matrix describe the same
    neighbourhoods, so CPRR must produce the same ranked lists from all of them."""
    results = {}
    for name, kwargs in {
        "rk_num": {},
        "rk_str": dict(input_file=data["rk_str"], rk_format="STR"),
        "dist": dict(input_file=data["matrix_dist"], input_format="MATRIX"),
    }.items():
        out = tmp_path / f"out_{name}"
        inp = make_input(udlf_template, data, "CPRR", METHOD_CASES["CPRR"], out,
                         tmp_path / f"log_{name}.txt", **kwargs)
        assert old_api.run(inp, get_output=True)
        results[name] = Path(f"{out}.txt").read_text()

    assert results["rk_num"] == results["rk_str"] == results["dist"]


def test_run_user_config_file(old_api, udlf_bin, data, tmp_path):
    """A user-provided config.ini runs as-is through runWithConfig."""
    out, log = tmp_path / "user_out", tmp_path / "user_log.txt"
    cfg = tmp_path / "user_config.ini"
    cfg.write_text(base_config(data, "CPRR", METHOD_CASES["CPRR"], out, log))

    output = old_api.runWithConfig(str(cfg), get_output=True)

    assert output
    assert Path(f"{out}.txt").is_file()
    before, after = parse_map(log)
    assert float(output.log_dict["MAP"]["After"]) == pytest.approx(after)
    assert after > before


def test_get_rks_returns_output_file_contents(old_api, udlf_template, data, tmp_path):
    out = tmp_path / "out"
    inp = make_input(udlf_template, data, "CPRR", METHOD_CASES["CPRR"], out,
                     tmp_path / "log.txt")
    output = old_api.run(inp, get_output=True)

    expected = [[int(x) for x in line.split()]
                for line in Path(f"{out}.txt").read_text().splitlines()]
    rks = output.get_rks(top_k=100)

    assert rks == expected
    assert len(rks) == 200 and all(len(r) == 100 for r in rks)
    assert all(r[0] == i for i, r in enumerate(rks[:10]))
