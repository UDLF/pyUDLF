"""
Sparse UDLF backend (pyUDLF.UDLF(backend="sparse") and pyUDLF.sparse).

Sparse UDLF gives the same ranked lists as UDLF 1.70, so the runs through
pyUDLF are compared with the UDLF backend, and with Sparse UDLF run directly
(see test_sparse_binary.py). Needs both binaries (scripts/build_sparse.sh);
otherwise these tests are skipped.
"""

import os
import random
import sys
from pathlib import Path

import numpy as np
import pytest

from conftest import N
from pyUDLF import UDLF, UDLFNotFoundError, UDLFParamError, UDLFRunError, sparse
from test_sparse_binary import run_sparse, sparse_config

PARAMS = {
    "CPRR": {"l": 100, "k": 10, "t": 2},
    "LHRR": {"l": 100, "k": 10, "t": 2},
    "RDPAC": {"l": 50, "k_end": 10},
    "BFSTREE": {"l": 100, "k": 10},
}


@pytest.fixture
def backend(sparse_dir):
    return UDLF(bin_path=str(sparse_dir), backend="sparse")


@pytest.fixture
def reference(udlf_bin):
    return UDLF(bin_path=str(udlf_bin))


@pytest.fixture(scope="session")
def rks(data):
    return np.loadtxt(data["rk_num"], dtype=np.int64)


@pytest.fixture(scope="session")
def labels(data):
    return [token.split(":")[1] for token in Path(data["classes"]).read_text().split()]


# --------------------------------------------------------------------------
# Same results as UDLF 1.70
# --------------------------------------------------------------------------

@pytest.mark.parametrize("method", sorted(PARAMS))
def test_run_matches_udlf(method, backend, reference, rks, labels):
    res = backend.run(method, ranked_lists=rks, params=PARAMS[method], classes=labels)
    original = reference.run(method, ranked_lists=rks, params=PARAMS[method], classes=labels)

    np.testing.assert_array_equal(res.ranked_lists, original.ranked_lists)
    assert res.method == sparse.method_name(method)[1]
    for section in ("before", "after"):
        # UDLF 1.70 rounds its float32 measures to 4 decimals
        assert res.metrics[section] == pytest.approx(original.metrics[section], abs=1.5e-4)
        assert res.raw_metrics[section] == pytest.approx(res.metrics[section], abs=1.5e-4)
    assert res.warnings == []


def test_run_matches_direct_run(backend, sparse_dir, data, tmp_path, rks, labels):
    res = backend.run("CPRR", ranked_lists=rks, params=PARAMS["CPRR"], classes=labels)
    proc = run_sparse(sparse_dir, "udlf", sparse_config(data, "CPRR_SPARSE", tmp_path), tmp_path)
    assert proc.returncode == 0
    np.testing.assert_array_equal(res.ranked_lists, np.loadtxt(tmp_path / "out.txt"))


@pytest.mark.parametrize("name", ["CPRR_SPARSE", "cprr", "Cprr_Sparse"])
def test_udlf_or_sparse_names(name, backend, rks):
    res = backend.run(name, ranked_lists=rks, params=PARAMS["CPRR"])
    assert res.method == "CPRR_SPARSE"


def test_bfstree_names(backend, rks):
    by_udlf_name = backend.run("BFSTREE", ranked_lists=rks, params=PARAMS["BFSTREE"])
    by_sparse_name = backend.run("BFSTree", ranked_lists=rks, params=PARAMS["BFSTREE"])
    np.testing.assert_array_equal(by_udlf_name.ranked_lists, by_sparse_name.ranked_lists)


def test_per_query_reproduces_the_metrics(backend, rks, labels):
    res = backend.run("LHRR", ranked_lists=rks, params=PARAMS["LHRR"], classes=labels)
    before, after = res.per_query()
    assert before.mean() == pytest.approx(res.map_before, abs=1e-4)
    assert after.mean() == pytest.approx(res.map_after, abs=1e-4)


def test_without_classes(backend, rks):
    res = backend.run("CPRR", ranked_lists=rks, params=PARAMS["CPRR"])
    assert res.metrics == {} and res.raw_metrics == {}
    assert res.ranked_lists.shape == (N, 100)


def test_classes_file_in_another_order(backend, data, tmp_path, rks, labels):
    """Sparse UDLF matches the classes by name, like pyUDLF."""
    lines = Path(data["classes"]).read_text().splitlines()
    random.Random(0).shuffle(lines)
    shuffled = tmp_path / "classes_shuffled.txt"
    shuffled.write_text("\n".join(lines) + "\n")

    from_file = backend.run("CPRR", ranked_lists=rks, params=PARAMS["CPRR"],
                            classes=str(shuffled), names=data["lists"])
    from_labels = backend.run("CPRR", ranked_lists=rks, params=PARAMS["CPRR"], classes=labels)

    assert from_file.metrics == from_labels.metrics
    assert from_file.raw_metrics == from_labels.raw_metrics


def test_more_threads_give_the_same_lists(sparse_dir, rks):
    one = UDLF(bin_path=str(sparse_dir), backend="sparse", threads=1)
    four = UDLF(bin_path=str(sparse_dir), backend="sparse", threads=4)
    for method in ("LHRR", "RDPAC"):
        np.testing.assert_array_equal(
            one.run(method, ranked_lists=rks, params=PARAMS[method]).ranked_lists,
            four.run(method, ranked_lists=rks, params=PARAMS[method]).ranked_lists)


def test_threads_set_the_lhrr_threads(sparse_dir, rks):
    res = UDLF(bin_path=str(sparse_dir), backend="sparse", threads=3).run(
        "LHRR", ranked_lists=rks, params=PARAMS["LHRR"])
    assert "PARAM_LHRR_SPARSE_THREADS = 3" in res.config
    res = UDLF(bin_path=str(sparse_dir), backend="sparse", threads=3).run(
        "LHRR", ranked_lists=rks, params=dict(PARAMS["LHRR"], threads=2))
    assert "PARAM_LHRR_SPARSE_THREADS = 2" in res.config


def test_sparse_only_parameters(backend, rks):
    res = backend.run("BFSTREE", ranked_lists=rks, params=dict(PARAMS["BFSTREE"], b=16,
                                                                memory_budget_mb=512))
    assert "PARAM_BFSTree_B = 16" in res.config
    assert "PARAM_BFSTree_MEMORY_BUDGET_MB = 512" in res.config
    with pytest.raises(UDLFParamError, match="positive int"):
        backend.run("BFSTREE", ranked_lists=rks, params={"b": 0})


# --------------------------------------------------------------------------
# RFE
# --------------------------------------------------------------------------

def test_rfe_failure_is_explained(backend, rks):
    with pytest.raises(UDLFRunError, match="Validator.hpp"):
        backend.run("RFE", ranked_lists=rks, params={"l": 100, "k": 10})


def test_rfe_runs_without_connected_components(backend):
    values, warnings = backend._sparse_params("RFE", "RFE", {"l": 100})
    assert values["PARAM_RFE_PERFORM_CCS"] == "FALSE"
    assert "perform_ccs=False" in warnings[0]
    assert not any(name.endswith(("_PATH", "_EMB", "_EMBEDDINGS")) for name in values)

    values, warnings = backend._sparse_params("RFE", "RFE", {"perform_ccs": False})
    assert warnings == []


@pytest.mark.parametrize("params, message", [
    ({"perform_ccs": True}, "perform_ccs=True"),
    ({"rerank_by_emb": True}, "rerank_by_emb"),
    ({"embeddings_path": "x.txt"}, "embeddings_path"),
])
def test_rfe_options_not_ported(backend, params, message):
    with pytest.raises(UDLFParamError, match=message):
        backend._sparse_params("RFE", "RFE", params)


# --------------------------------------------------------------------------
# Files
# --------------------------------------------------------------------------

def test_files_are_kept_on_request(backend, rks, labels):
    res = backend.run("CPRR", ranked_lists=rks, params=PARAMS["CPRR"], classes=labels,
                      keep_files=True)
    assert set(res.files) == {"config", "log", "lists", "classes", "output"}
    assert all(Path(p).is_file() for p in res.files.values())
    work = Path(res.files["config"]).parent
    assert (work / "scratch").is_dir()       # UDLF_TMPDIR of the run


def test_no_temporary_files_are_left(backend, rks, tmp_path):
    backend.run("CPRR", ranked_lists=rks, params=PARAMS["CPRR"])
    assert not list(tmp_path.glob("pyudlf_*"))  # tempfile is redirected to tmp_path


# --------------------------------------------------------------------------
# run_config
# --------------------------------------------------------------------------

@pytest.mark.parametrize("method", ["CPRR_SPARSE", "RDPAC"])
def test_run_config(method, backend, reference, data, tmp_path, monkeypatch, rks, labels):
    """The binary is picked from UDL_METHOD (RDPAC needs the strict one)."""
    user = tmp_path / "user"
    user.mkdir()
    cfg = user / "config.ini"
    cfg.write_text(sparse_config(data, method, user))
    monkeypatch.chdir(user)

    res = backend.run_config(cfg)

    base = sparse.method_name(method)[0]
    params = {"CPRR": PARAMS["CPRR"], "RDPAC": PARAMS["RDPAC"]}[base]
    original = reference.run(base, ranked_lists=rks, params=params, classes=labels,
                             precisions=[5, 10, 20], recalls=[5, 10, 20])
    np.testing.assert_array_equal(res.ranked_lists, original.ranked_lists)
    assert res.files["ranked_lists"] == str(user / "out.txt")
    assert res.metrics["after"] == pytest.approx(original.metrics["after"], abs=1.5e-4)


def test_run_config_matrix_output_is_reported(backend, data, tmp_path, monkeypatch):
    cfg = tmp_path / "config.ini"
    cfg.write_text(sparse_config(data, "CPRR_SPARSE", tmp_path).replace(
        "OUTPUT_FILE_FORMAT = RK", "OUTPUT_FILE_FORMAT = MATRIX"))
    monkeypatch.chdir(tmp_path)

    res = backend.run_config(cfg)

    assert res.matrix.shape == (N, N) and res.ranked_lists is None
    assert any("all zeros" in w for w in res.warnings)


# --------------------------------------------------------------------------
# Errors
# --------------------------------------------------------------------------

@pytest.mark.parametrize("kwargs, message", [
    (dict(method="RLSIM"), "implements only"),
    (dict(matrix=np.eye(N), ranked_lists=None), "only ranked lists"),
    (dict(output="matrix"), "all-zero"),
    (dict(params={"l": 100, "k": 150}), "larger than l"),
    (dict(params={"l": N + 1}), "larger than the dataset"),
    (dict(params={"kk": 1}), "Unknown parameter"),
])
def test_invalid_runs(backend, rks, kwargs, message):
    arguments = dict(dict(method="CPRR", ranked_lists=rks, params=PARAMS["CPRR"]), **kwargs)
    with pytest.raises(UDLFParamError, match=message):
        backend.run(**arguments)


def test_input_shorter_than_l(backend, rks):
    with pytest.raises(UDLFParamError, match="reads 100 per line"):
        backend.run("CPRR", ranked_lists=rks[:, :50], params=PARAMS["CPRR"])


def test_string_ranked_lists_and_fusion_are_not_supported(backend, data, rks):
    with pytest.raises(UDLFParamError, match="indices"):
        backend.run("CPRR", ranked_lists=data["rk_str"], names=data["lists"],
                    params=PARAMS["CPRR"])
    with pytest.raises(UDLFParamError, match="FUSION"):
        backend.fuse("CPRR", [rks, rks])


def test_backend_mismatch_is_detected(sparse_dir, udlf_bin):
    with pytest.raises(UDLFParamError, match="Sparse UDLF binary"):
        UDLF(bin_path=str(sparse_dir / "udlf"))
    with pytest.raises(UDLFParamError, match="is a UDLF binary"):
        UDLF(bin_path=str(udlf_bin), backend="sparse")
    with pytest.raises(UDLFParamError, match="backend must be"):
        UDLF(bin_path=str(udlf_bin), backend="gpu")


@pytest.mark.skipif(sys.platform == "win32", reason="the fake binary is a shell script")
def test_former_udlf_csr_is_rejected(tmp_path):
    """UDLF-CSR answered a missing config like Sparse UDLF, but exited with 0."""
    fake = tmp_path / "udlf"
    fake.write_text('#!/bin/sh\necho "Failed to open file: $1"\nexit 0\n')
    fake.chmod(0o755)
    with pytest.raises(UDLFParamError, match="former UDLF-CSR"):
        UDLF(bin_path=str(fake), backend="sparse")


def test_csr_is_an_alias(sparse_dir, rks):
    assert UDLF(bin_path=str(sparse_dir), backend="csr").backend == "sparse"


@pytest.mark.parametrize("variable", ["UDLF_SPARSE_BIN", "UDLF_CSR_BIN"])
def test_binaries_from_environment(variable, sparse_dir, monkeypatch):
    monkeypatch.delenv("UDLF_SPARSE_BIN", raising=False)
    monkeypatch.delenv("UDLF_CSR_BIN", raising=False)
    monkeypatch.setenv(variable, str(sparse_dir / "udlf_strict"))  # a binary or the directory
    backend = UDLF(backend="sparse")
    assert backend.binaries == {"udlf": str(sparse_dir / "udlf"),
                                "udlf_strict": str(sparse_dir / "udlf_strict")}
    monkeypatch.delenv(variable)
    with pytest.raises(UDLFNotFoundError, match="build_sparse.sh"):
        UDLF(backend="sparse")


def test_strict_binary_is_required_for_strict_methods(sparse_dir, tmp_path, rks):
    only_fast = tmp_path / "bin"
    only_fast.mkdir()
    (only_fast / "udlf").symlink_to(sparse_dir / "udlf")
    backend = UDLF(bin_path=str(only_fast), backend="sparse")

    assert backend.run("CPRR", ranked_lists=rks, params=PARAMS["CPRR"]).ranked_lists.shape \
        == (N, 100)
    with pytest.raises(UDLFNotFoundError, match="udlf_strict"):
        backend.run("RDPAC", ranked_lists=rks, params=PARAMS["RDPAC"])


def test_relative_binary_path(sparse_dir, rks, monkeypatch):
    """Sparse UDLF runs in the run directory, so a relative path must still work."""
    monkeypatch.chdir(sparse_dir.parent)
    backend = UDLF(bin_path=sparse_dir.name, backend="sparse")
    res = backend.run("CPRR", ranked_lists=rks, params=PARAMS["CPRR"])
    assert res.ranked_lists.shape == (N, 100)


@pytest.mark.parametrize("threads", [0, -1, 1.5, True, "2"])
def test_invalid_threads(sparse_dir, threads):
    with pytest.raises(UDLFParamError, match="threads"):
        UDLF(bin_path=str(sparse_dir), backend="sparse", threads=threads)


# --------------------------------------------------------------------------
# pyUDLF.sparse
# --------------------------------------------------------------------------

def test_parse_log_ignores_the_gains_block():
    log = ("EFFECTIVENESS BEFORE RERANKING\n P@10\t63.1%\n MAP\t54.7131\n\n"
           "EFFECTIVENESS AFTER RERANKING\n P@10\t83.15%\n MAP\t76.0246\n\n"
           "- RELATIVE GAINS -\n P@10\t31.775%\n MAP\t38.95%\n")
    parsed = sparse.parse_log(log)
    assert parsed["before"] == pytest.approx({"P@10": 0.631, "MAP": 0.547131})
    assert parsed["after"] == pytest.approx({"P@10": 0.8315, "MAP": 0.760246})


def test_udlf_values_renames_the_method():
    values = {"UDL_METHOD": "BFSTree", "PARAM_BFSTree_L": "100", "SIZE_DATASET": "200"}
    assert sparse.udlf_values(values) == {"UDL_METHOD": "BFSTREE", "PARAM_BFSTREE_L": "100",
                                          "SIZE_DATASET": "200"}
