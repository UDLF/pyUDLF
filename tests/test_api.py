"""
The high-level API (pyUDLF.UDLF) must give exactly the results of running the
UDLF binary directly, and the same results as the legacy API.
"""

import filecmp
import os
from pathlib import Path

import numpy as np
import pytest

from conftest import N, METHOD_CASES, base_config, make_input, parse_map, run_direct
from pyUDLF import (UDLF, UDLFError, UDLFNotFoundError, UDLFParamError, UDLFRunError)
from pyUDLF.utils.validations import METHOD_PARAMS


@pytest.fixture
def udlf(udlf_bin):
    return UDLF(bin_path=str(udlf_bin))


@pytest.fixture(scope="session")
def rks(data):
    return np.loadtxt(data["rk_num"], dtype=np.int64)


@pytest.fixture(scope="session")
def labels(data):
    return [token.split(":")[1] for token in Path(data["classes"]).read_text().split()]


def typed_params(method):
    """METHOD_CASES values (config strings) converted to Python types."""
    types = {spec["param"]: spec["type"] for spec in METHOD_PARAMS[method].values()}
    return {name: (value == "TRUE") if types[name] is bool else types[name](value)
            for name, value in METHOD_CASES[method].items()}


def direct(udlf_bin, data, tmp_path, method, params=None, tag="direct", **kwargs):
    """Run UDLF directly; return (output lists file, log file)."""
    out, log = tmp_path / tag, tmp_path / f"{tag}_log.txt"
    proc = run_direct(udlf_bin, base_config(data, method, params or METHOD_CASES[method],
                                            out, log, **kwargs), tmp_path)
    assert proc.returncode == 0, proc.stdout
    return Path(f"{out}.txt"), log


def as_array(path, dtype=np.int64):
    return np.loadtxt(path, dtype=dtype, ndmin=2)


# --------------------------------------------------------------------------
# Same results as UDLF
# --------------------------------------------------------------------------

@pytest.mark.parametrize("method", sorted(METHOD_CASES))
def test_run_matches_direct_run(udlf, udlf_bin, data, tmp_path, rks, labels, method):
    res = udlf.run(method, ranked_lists=rks, params=typed_params(method), classes=labels)

    out, log = direct(udlf_bin, data, tmp_path, method)
    np.testing.assert_array_equal(res.ranked_lists, as_array(out))
    assert (res.map_before, res.map_after) == parse_map(log)
    assert res.ranked_lists.dtype == np.int32


@pytest.mark.parametrize("variant", ["rk_file", "rk_str_file", "matrix_dist", "matrix_sim",
                                     "matrix_dist_file"])
def test_input_variants_match_direct_run(udlf, udlf_bin, data, tmp_path, rks, labels,
                                         variant):
    params = typed_params("CPRR")
    if variant == "rk_file":
        res = udlf.run("CPRR", ranked_lists=data["rk_num"], params=params, classes=labels)
        kwargs = {}
    elif variant == "rk_str_file":
        res = udlf.run("CPRR", ranked_lists=data["rk_str"], names=data["lists"],
                       params=params, classes=data["classes"])
        kwargs = dict(input_file=data["rk_str"], rk_format="STR")
    else:
        kind = "sim" if variant == "matrix_sim" else "dist"
        path = data[f"matrix_{kind}"]
        matrix = path if variant.endswith("_file") else np.loadtxt(path)
        res = udlf.run("CPRR", matrix=matrix, matrix_type=kind, params=params,
                       classes=labels)
        kwargs = dict(input_file=path, input_format="MATRIX", matrix_type=kind.upper())

    out, log = direct(udlf_bin, data, tmp_path, "CPRR", **kwargs)
    np.testing.assert_array_equal(res.ranked_lists, as_array(out))
    assert res.map_after == parse_map(log)[1]


@pytest.mark.parametrize("kind", ["dist", "sim"])
def test_matrix_output_matches_direct_run(udlf, udlf_bin, data, tmp_path, rks, kind):
    res = udlf.run("CPRR", ranked_lists=rks, params=typed_params("CPRR"),
                   output="matrix", output_matrix_type=kind)

    params = dict(METHOD_CASES["CPRR"], OUTPUT_FILE_FORMAT="MATRIX",
                  OUTPUT_MATRIX_TYPE=kind.upper())
    out, _ = direct(udlf_bin, data, tmp_path, "CPRR", params)
    assert res.ranked_lists is None
    np.testing.assert_array_equal(res.matrix, as_array(out, np.float64))
    assert res.matrix.shape == (N, N)


def test_fuse_matches_direct_run(udlf, udlf_bin, data, tmp_path, rks, labels):
    sim = np.loadtxt(data["matrix_sim"])
    rk_sim = np.argsort(-sim, axis=1, kind="stable")
    rk_sim_file = tmp_path / "rk_sim.txt"
    np.savetxt(rk_sim_file, rk_sim, fmt="%d")

    res = udlf.fuse("CPRR", [rks, rk_sim], params=typed_params("CPRR"), classes=labels)

    params = dict(METHOD_CASES["CPRR"], UDL_TASK="FUSION", NUM_INPUT_FUSION_FILES="2",
                  INPUT_FILES_FUSION_1=data["rk_num"], INPUT_FILES_FUSION_2=str(rk_sim_file))
    out, log = direct(udlf_bin, data, tmp_path, "CPRR", params)
    np.testing.assert_array_equal(res.ranked_lists, as_array(out))
    assert set(res.metrics) == {"after"}
    assert res.map_after == pytest.approx(
        float(Path(log).read_text().split("MAP")[-1].split()[0]))


def test_run_config_matches_direct_run(udlf, udlf_bin, data, tmp_path):
    out, log = tmp_path / "user_out", tmp_path / "user_log.txt"
    cfg = tmp_path / "user_config.ini"
    cfg.write_text(base_config(data, "CPRR", METHOD_CASES["CPRR"], out, log))

    res = udlf.run_config(cfg)

    direct_out, direct_log = direct(udlf_bin, data, tmp_path, "CPRR")
    np.testing.assert_array_equal(res.ranked_lists, as_array(direct_out))
    assert (res.map_before, res.map_after) == parse_map(direct_log)
    assert res.files["ranked_lists"] == f"{out}.txt"
    assert res.config == cfg.read_text()
    before, after = res.per_query()
    assert (round(before.mean(), 4), round(after.mean(), 4)) == parse_map(direct_log)


def test_same_results_as_legacy_api(udlf, old_api, udlf_template, data, tmp_path, rks,
                                    labels):
    inp = make_input(udlf_template, data, "LHRR", METHOD_CASES["LHRR"],
                     tmp_path / "legacy", tmp_path / "legacy_log.txt")
    legacy = old_api.run(inp, get_output=True)

    res = udlf.run("LHRR", ranked_lists=rks, params=typed_params("LHRR"), classes=labels)

    np.testing.assert_array_equal(res.ranked_lists, as_array(f"{tmp_path / 'legacy'}.txt"))
    assert res.map_after == legacy.log_dict["MAP"]["After"]
    assert res.metrics["after"]["P@10"] == legacy.log_dict["P@10"]["After"]


# --------------------------------------------------------------------------
# Results
# --------------------------------------------------------------------------

def test_result_contents(udlf, rks, labels):
    res = udlf.run("CPRR", ranked_lists=rks, params={"l": 100, "k": 10}, classes=labels)

    assert set(res.metrics) == {"before", "after", "gain"}
    assert set(res.metrics["after"]) == {"P@4", "P@5", "P@10", "P@15", "P@20", "P@30",
                                         "P@50", "P@100", "Recall@4", "Recall@5",
                                         "Recall@10", "Recall@20", "Recall@40", "MAP"}
    assert res.metrics["gain"]["MAP"] == pytest.approx(
        (res.map_after - res.map_before) / res.map_before * 100, abs=0.01)
    assert isinstance(res.time, float)
    assert "UDL_METHOD = CPRR" in res.config
    assert "Execution Completed!" in res.stdout
    assert res.files == {}
    assert "MAP" in repr(res)


@pytest.mark.parametrize("input_kind", ["ranked_lists", "matrix"])
def test_per_query_reproduces_udlf_map(udlf, data, rks, labels, input_kind):
    if input_kind == "ranked_lists":
        res = udlf.run("RDPAC", ranked_lists=rks, params=typed_params("RDPAC"),
                       classes=labels)
    else:
        res = udlf.run("RDPAC", matrix=np.loadtxt(data["matrix_dist"]),
                       params=typed_params("RDPAC"), classes=labels)

    before, after = res.per_query("MAP")
    assert before.shape == after.shape == (N,)
    assert before.mean() == pytest.approx(res.map_before, abs=1.5e-4)
    assert after.mean() == pytest.approx(res.map_after, abs=1.5e-4)
    _, precision_after = res.per_query("precision", depth=10)
    assert precision_after.mean() == pytest.approx(res.metrics["after"]["P@10"], abs=1.5e-4)


def test_default_precisions_fit_the_output_size(udlf, rks, labels):
    res = udlf.run("CPRR", ranked_lists=rks, params={"l": 30, "k": 10}, classes=labels)

    assert {k for k in res.metrics["after"] if k.startswith("P@")} == \
        {"P@4", "P@5", "P@10", "P@15", "P@20", "P@30"}


def test_explicit_precisions_and_recalls(udlf, rks, labels):
    res = udlf.run("CPRR", ranked_lists=rks, params={"l": 100, "k": 10}, classes=labels,
                   precisions=[1, 7], recalls=[3])

    assert set(res.metrics["after"]) == {"P@1", "P@7", "Recall@3", "MAP"}


def test_without_classes_there_is_no_evaluation(udlf, rks, caplog):
    res = udlf.run("CPRR", ranked_lists=rks, params={"l": 100, "k": 10})

    assert res.metrics == {} and res.map_after is None
    assert res.ranked_lists.shape == (N, 100)
    assert "evaluation is disabled" in caplog.text
    with pytest.raises(UDLFError, match="classes"):
        res.per_query()


def test_string_and_numeric_labels_give_the_same_results(udlf, data, rks, labels):
    numeric = udlf.run("CPRR", ranked_lists=rks, params={"l": 100}, classes=labels)
    textual = udlf.run("CPRR", ranked_lists=rks, params={"l": 100},
                       classes=[f"class_{x}" for x in labels])
    from_files = udlf.run("CPRR", ranked_lists=rks, params={"l": 100},
                          classes=data["classes_str"], names=data["lists"])

    assert numeric.metrics == textual.metrics == from_files.metrics


# --------------------------------------------------------------------------
# Files
# --------------------------------------------------------------------------

def test_files_are_removed_by_default(udlf, rks, tmp_path):
    udlf.run("CPRR", ranked_lists=rks, params={"l": 100})
    assert not list(tmp_path.glob("pyudlf_*"))  # tempfile is redirected to tmp_path


def test_keep_files(udlf, rks, labels):
    res = udlf.run("CPRR", ranked_lists=rks, params={"l": 100}, classes=labels,
                   keep_files=True)

    assert set(res.files) == {"config", "log", "lists", "output", "classes"}
    assert all(Path(p).is_file() for p in res.files.values())
    assert Path(res.files["config"]).read_text() == res.config


def test_workdir(udlf_bin, rks, tmp_path):
    udlf = UDLF(bin_path=str(udlf_bin), workdir=tmp_path / "runs")
    res = udlf.run("CPRR", ranked_lists=rks, params={"l": 100})

    assert Path(res.files["output"]).parent == tmp_path / "runs"


def test_input_files_are_used_in_place(udlf, data):
    res = udlf.run("CPRR", ranked_lists=data["rk_num"], params={"l": 100})
    assert f"INPUT_FILE = {data['rk_num']}" in res.config


# --------------------------------------------------------------------------
# Errors
# --------------------------------------------------------------------------

@pytest.mark.parametrize("kwargs, message", [
    (dict(method="NOT_A_METHOD"), "Unknown method"),
    (dict(params={"alpha": 1}), "Unknown parameter"),
    (dict(params={"k": "10"}), "must be int"),
    (dict(params={"k": True}), "must be int"),
    (dict(params={"l": N + 1}), "larger than the dataset"),
    (dict(precisions=[5, 200]), "larger than the output"),
    (dict(precisions=[0]), "positive"),
    (dict(names=["a b"] * N), "spaces"),
    (dict(classes=[1, 2]), "labels"),
    (dict(output="html"), "output must be"),
])
def test_invalid_arguments_raise_before_running(udlf, rks, labels, kwargs, message):
    kwargs = dict(dict(method="CPRR", ranked_lists=rks, params={"l": 100},
                       classes=labels), **kwargs)
    with pytest.raises(UDLFParamError, match=message):
        udlf.run(**kwargs)


def test_ranked_lists_shorter_than_l_raise(udlf, rks):
    with pytest.raises(UDLFParamError, match="reads 100 per line"):
        udlf.run("CPRR", ranked_lists=rks[:, :50], params={"l": 100})


def test_input_must_be_ranked_lists_or_matrix(udlf, rks):
    with pytest.raises(UDLFParamError, match="exactly one"):
        udlf.run("CPRR", ranked_lists=rks, matrix=np.eye(N))
    with pytest.raises(UDLFParamError, match="integer"):
        udlf.run("CPRR", ranked_lists=rks.astype(float))
    with pytest.raises(UDLFParamError, match="indices"):
        udlf.run("CPRR", ranked_lists=rks + 1)


def test_udlf_failure_raises_run_error(udlf, rks):
    with pytest.raises(UDLFRunError) as info:
        udlf.run("CPRR", ranked_lists=rks, params={"l": 100, "k": 150})  # K > L

    assert info.value.problems == ["UDLF exited with code 1"]
    assert "K can't be greater than L" in str(info.value)
    assert "PARAM_CPRR_K = 150" in info.value.config


def test_fuse_arguments(udlf, rks):
    with pytest.raises(UDLFParamError, match="does not support FUSION"):
        udlf.fuse("BFSTREE", [rks, rks])
    with pytest.raises(UDLFParamError, match="at least two"):
        udlf.fuse("CPRR", [rks])


def test_missing_binary(tmp_path, monkeypatch):
    with pytest.raises(UDLFNotFoundError, match="bin_path"):
        UDLF(bin_path=tmp_path / "udlf")
    monkeypatch.setenv("UDLF_BIN", str(tmp_path / "env_udlf"))
    with pytest.raises(UDLFNotFoundError, match="UDLF_BIN"):
        UDLF()


def test_binary_from_environment(udlf_bin, monkeypatch):
    monkeypatch.setenv("UDLF_BIN", str(udlf_bin))
    assert UDLF().bin_path == str(udlf_bin)


def test_errors_are_also_builtin_exceptions():
    assert issubclass(UDLFParamError, ValueError)
    assert issubclass(UDLFNotFoundError, FileNotFoundError)
    assert issubclass(UDLFRunError, RuntimeError)


# --------------------------------------------------------------------------
# Information
# --------------------------------------------------------------------------

def test_methods_and_describe():
    assert UDLF.methods() == sorted(METHOD_PARAMS)
    text = UDLF.describe("rlsim")
    assert "metric = 'INTERSECTION'" in text and "KENDALL_TAU" in text
