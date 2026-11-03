"""
How the legacy API decides that a UDLF run failed.

A run fails when:
  - the inputs cannot be read correctly by UDLF (checked before running);
  - UDLF exits with a non-zero code or is killed by a signal;
  - UDLF replaces a value set by the user with its default.
Nothing else (e.g. words such as "error" in a path) makes a run fail.
"""

import logging
from pathlib import Path

import pytest

from conftest import METHOD_CASES, N, base_config, make_input


def _cprr_input(udlf_template, data, tmp_path, **kwargs):
    return make_input(udlf_template, data, "CPRR", METHOD_CASES["CPRR"],
                      tmp_path / "out", tmp_path / "log.txt", **kwargs)


def _write_truncated(src, dst, columns=None, rows=None):
    lines = Path(src).read_text().splitlines()[:rows]
    dst.write_text("".join(" ".join(l.split()[:columns]) + "\n" for l in lines))
    return dst


# --------------------------------------------------------------------------
# verify_running: return code and output of the UDLF process
# --------------------------------------------------------------------------

def test_verify_running_accepts_clean_run(old_api):
    assert old_api.verify_running(0, " *WARNING: You haven't declared X!\n") == []


@pytest.mark.parametrize("returncode, expected", [
    (1, "exited with code 1"),
    (-11, "segmentation fault"),
    (-9, "killed by signal 9"),
])
def test_verify_running_reports_return_code(old_api, returncode, expected):
    problems = old_api.verify_running(returncode, "")
    assert len(problems) == 1 and expected in problems[0]


@pytest.mark.parametrize("line, name", [
    (" *WARNING: You've declared PARAM_RLSIM_METRIC = FOO! Expected values are: "
     "[INTERSECTION,RBO,]", "PARAM_RLSIM_METRIC"),
    (" *WARNING: Type of PARAM_CPRR_K is UINT! abc is invalid!", "PARAM_CPRR_K"),
])
def test_verify_running_reports_values_replaced_by_default(old_api, line, name):
    problems = old_api.verify_running(0, line + "\n *SETTING: ...\n")
    assert len(problems) == 1 and name in problems[0]


# --------------------------------------------------------------------------
# End-to-end
# --------------------------------------------------------------------------

def test_path_containing_word_error_runs(old_api, udlf_template, data, tmp_path):
    """Words like 'error' or 'invalid' in a path must not make a run fail."""
    folder = tmp_path / "error_invalid_unable"
    folder.mkdir()
    rk = folder / "rk.txt"
    rk.write_text(Path(data["rk_num"]).read_text())
    inp = _cprr_input(udlf_template, data, tmp_path, input_file=str(rk))

    assert old_api.run(inp, get_output=True)


def test_udlf_abort_is_reported(old_api, udlf_template, data, tmp_path, caplog):
    inp = _cprr_input(udlf_template, data, tmp_path)
    inp.set_param("PARAM_CPRR_K", 150)  # UDLF aborts: K > L (L = 100)

    assert old_api.run(inp, get_output=True) is False
    assert "exited with code 1" in caplog.text
    assert "K can't be greater than L" in caplog.text  # tail of UDLF output


def test_value_replaced_by_default_is_reported(old_api, data, tmp_path, caplog):
    """A user config with an invalid enum: UDLF uses the default and exits 0.
    (set_param rejects such values earlier; a config file bypasses it.)"""
    params = dict(METHOD_CASES["RLSIM"], PARAM_RLSIM_METRIC="NOT_A_METRIC")
    cfg = tmp_path / "user_config.ini"
    cfg.write_text(base_config(data, "RLSIM", params, tmp_path / "out", tmp_path / "log"))

    assert old_api.runWithConfig(str(cfg), get_output=True) is False
    assert "PARAM_RLSIM_METRIC = 'NOT_A_METRIC'" in caplog.text


def test_no_temporary_files_are_left(old_api, udlf_template, data, tmp_path):
    """tempfile is redirected to tmp_path by conftest."""
    ok = _cprr_input(udlf_template, data, tmp_path)
    assert old_api.run(ok, get_output=False)
    bad = _cprr_input(udlf_template, data, tmp_path)
    bad.set_param("PARAM_CPRR_K", 150)  # UDLF aborts: K > L
    assert old_api.run(bad, get_output=True) is False

    leftovers = sorted(p.name for p in tmp_path.iterdir())
    assert leftovers == ["log.txt", "out.txt"]


def test_successful_run_keeps_udlf_output(old_api, udlf_template, data, tmp_path):
    output = old_api.run(_cprr_input(udlf_template, data, tmp_path), get_output=True)
    assert "Execution Completed!" in output.stdout


# --------------------------------------------------------------------------
# Inputs checked before running
# --------------------------------------------------------------------------

def test_ranked_lists_shorter_than_l_are_rejected(old_api, udlf_template, data, tmp_path,
                                                  caplog):
    """UDLF reads L elements per line: with shorter lines it keeps reading the
    next lines, then repeats the last value, and still exits with code 0
    (on the synthetic data: MAP 0.5489 -> 0.5810 over garbage lists)."""
    short = _write_truncated(data["rk_num"], tmp_path / "rk_short.txt", columns=20)
    inp = _cprr_input(udlf_template, data, tmp_path, input_file=str(short))

    assert old_api.run(inp, get_output=True) is False
    assert "reads 100 per line" in caplog.text
    assert not (tmp_path / "out.txt").exists()  # UDLF was not executed


def test_ranked_lists_with_fewer_lines_than_dataset_are_rejected(
        old_api, udlf_template, data, tmp_path, caplog):
    short = _write_truncated(data["rk_num"], tmp_path / "rk_rows.txt", rows=N - 1)
    inp = _cprr_input(udlf_template, data, tmp_path, input_file=str(short))

    assert old_api.run(inp, get_output=True) is False
    assert f"has {N - 1} lines, but SIZE_DATASET = {N}" in caplog.text


@pytest.mark.parametrize("method, params, required", [
    ("CPRR", {"PARAM_CPRR_L": "100"}, 100),
    ("CONTEXTRR", {"PARAM_CONTEXTRR_L": "25"}, N),   # reads full lists
    ("RLSIM", {"PARAM_RLSIM_CK": "100"}, N),         # reads full lists
    ("RDPAC", {"PARAM_RDPAC_L": "50", "PARAM_RDPAC_L_MULT": "2"}, 100),
])
def test_required_columns_per_method(old_api, data, tmp_path, method, params, required):
    rk = tmp_path / "rk.txt"
    cfg = tmp_path / "cfg.ini"
    for columns, should_pass in [(required, True), (required - 1, False)]:
        _write_truncated(data["rk_num"], rk, columns=columns)
        cfg.write_text(base_config(data, method, params, tmp_path / "o", tmp_path / "l",
                                   input_file=str(rk)))
        assert (old_api.check_input_files(str(cfg)) == []) is should_pass


def test_matrix_inputs_are_not_checked_for_width(old_api, data, tmp_path):
    cfg = tmp_path / "cfg.ini"
    cfg.write_text(base_config(data, "CPRR", METHOD_CASES["CPRR"], tmp_path / "o",
                               tmp_path / "l", input_file=data["matrix_dist"],
                               input_format="MATRIX"))
    assert old_api.check_input_files(str(cfg)) == []


def test_config_values_are_read_like_udlf(tmp_path):
    from pyUDLF.utils.parser import read_config_values

    cfg = tmp_path / "cfg.ini"
    cfg.write_text("# comment\nUDL_METHOD = CPRR   # trailing comment\n"
                   "PARAM_CPRR_L =\t400\nPARAM_CPRR_L = 200\nNO_ASSIGNMENT\n")
    assert read_config_values(str(cfg)) == {"UDL_METHOD": "CPRR", "PARAM_CPRR_L": "200"}


# --------------------------------------------------------------------------
# Binary / config paths
# --------------------------------------------------------------------------

def test_missing_binary_path_raises(old_api, tmp_path):
    with pytest.raises(FileNotFoundError):
        old_api.setBinaryPath(str(tmp_path / "does_not_exist" / "udlf"))


def test_missing_config_path_raises(old_api, tmp_path):
    with pytest.raises(FileNotFoundError):
        old_api.setConfigPath(str(tmp_path / "does_not_exist.ini"))


def test_set_binary_path_accepts_existing_file(old_api, udlf_bin, monkeypatch):
    monkeypatch.setattr(old_api, "bin_path", "/somewhere/else")
    old_api.setBinaryPath(str(udlf_bin))
    assert old_api.getBinaryPath() == str(udlf_bin)
