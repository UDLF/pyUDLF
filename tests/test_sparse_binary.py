"""
Characterization of the Sparse UDLF binaries (https://github.com/andreTomi/Sparse_UDLF,
commit de3c14c), run directly on configs written by hand: what pyUDLF relies on.

Sparse UDLF builds two binaries: bin/udlf (fast-math; CPRR_SPARSE, LHRR_SPARSE)
and bin/udlf_strict (every method; RDPAC, RFE and BFSTree refuse fast-math).
On the synthetic dataset its ranked lists are byte-identical to UDLF 1.70.
"""

import os
import subprocess
from pathlib import Path

import numpy as np
import pytest

from conftest import METHOD_CASES, N, base_config, run_direct

# Sparse UDLF method -> (UDLF 1.70 method, binary). Parameters are those of
# METHOD_CASES, renamed (PARAM_CPRR_K -> PARAM_CPRR_SPARSE_K).
METHODS = {
    "CPRR_SPARSE": ("CPRR", "udlf"),
    "LHRR_SPARSE": ("LHRR", "udlf"),
    "RDPAC": ("RDPAC", "udlf_strict"),
    "BFSTree": ("BFSTREE", "udlf_strict"),
    "RFE": ("RFE", "udlf_strict"),
}
# Parameters of UDLF 1.70 that Sparse UDLF does not have
NOT_PORTED = {"PARAM_RFE_EMBEDDINGS_PATH", "PARAM_RFE_CCS_PATH"}


def sparse_params(method):
    base = METHODS[method][0]
    return {key.replace(f"PARAM_{base}_", f"PARAM_{method}_", 1): value
            for key, value in METHOD_CASES[base].items() if key not in NOT_PORTED}


def run_sparse(sparse_dir, binary, config_text, workdir, threads=1, env=None):
    workdir = Path(workdir)
    workdir.mkdir(parents=True, exist_ok=True)
    cfg = workdir / "config.ini"
    cfg.write_text(config_text)
    environment = dict(os.environ, OMP_NUM_THREADS=str(threads), **(env or {}))
    return subprocess.run([str(sparse_dir / binary), str(cfg)], capture_output=True,
                          text=True, cwd=workdir, env=environment)


def sparse_config(data, method, workdir, **extra):
    workdir = Path(workdir)
    params = {**sparse_params(method), **extra}
    return base_config(data, method, params, workdir / "out.txt", workdir / "log.txt")


def udlf_reference(udlf_bin, data, base, workdir):
    workdir = Path(workdir)
    workdir.mkdir(parents=True, exist_ok=True)
    proc = run_direct(udlf_bin, base_config(data, base, METHOD_CASES[base], workdir / "out",
                                            workdir / "log.txt"), workdir)
    assert proc.returncode == 0, proc.stdout
    return np.loadtxt(workdir / "out.txt", dtype=np.int64)


@pytest.mark.parametrize("method", [m for m in METHODS if m != "RFE"])
def test_lists_identical_to_udlf(method, sparse_dir, udlf_bin, data, tmp_path):
    base, binary = METHODS[method]
    proc = run_sparse(sparse_dir, binary, sparse_config(data, method, tmp_path / "s"),
                      tmp_path / "s")
    assert proc.returncode == 0, proc.stdout + proc.stderr

    lists = np.loadtxt(tmp_path / "s" / "out.txt", dtype=np.int64)
    assert np.array_equal(lists, udlf_reference(udlf_bin, data, base, tmp_path / "u"))


@pytest.mark.xfail(strict=True, reason="Sparse UDLF de3c14c: PARAM_RFE_PERFORM_CCS, "
                   "_RERANK_BY_EMB and _EXPORT_EMBEDDINGS are commented out in Validator.hpp, "
                   "so the parser drops them and RFE stops with 'Missing method parameter'")
def test_rfe_identical_to_udlf(sparse_dir, udlf_bin, data, tmp_path):
    proc = run_sparse(sparse_dir, "udlf_strict", sparse_config(data, "RFE", tmp_path / "s"),
                      tmp_path / "s")
    assert proc.returncode == 0, proc.stdout + proc.stderr
    lists = np.loadtxt(tmp_path / "s" / "out.txt", dtype=np.int64)
    assert np.array_equal(lists, udlf_reference(udlf_bin, data, "RFE", tmp_path / "u"))


def test_rfe_fails_with_missing_parameter(sparse_dir, data, tmp_path):
    proc = run_sparse(sparse_dir, "udlf_strict", sparse_config(data, "RFE", tmp_path),
                      tmp_path)
    assert proc.returncode == 1
    assert "Unknown param PARAM_RFE_PERFORM_CCS" in proc.stderr
    assert "Missing method parameter: PARAM_RFE_PERFORM_CCS" in proc.stdout


@pytest.mark.parametrize("method", ["RDPAC", "BFSTree", "RFE"])
def test_fast_math_binary_refuses_strict_methods(method, sparse_dir, data, tmp_path):
    proc = run_sparse(sparse_dir, "udlf", sparse_config(data, method, tmp_path), tmp_path)
    assert proc.returncode == 1
    assert "compiled with -ffast-math" in proc.stdout
    assert "bin/udlf_strict" in proc.stdout


@pytest.mark.parametrize("method", ["CPRR_SPARSE", "LHRR_SPARSE"])
def test_fast_math_and_strict_binaries_agree(method, sparse_dir, data, tmp_path):
    lists = []
    for binary in ("udlf", "udlf_strict"):
        work = tmp_path / binary
        proc = run_sparse(sparse_dir, binary, sparse_config(data, method, work), work)
        assert proc.returncode == 0, proc.stdout
        lists.append(np.loadtxt(work / "out.txt", dtype=np.int64))
    assert np.array_equal(*lists)


@pytest.mark.parametrize("method", ["CPRR_SPARSE", "LHRR_SPARSE", "RDPAC", "BFSTree"])
def test_results_do_not_depend_on_threads(method, sparse_dir, data, tmp_path):
    binary = METHODS[method][1]
    extra = {"PARAM_LHRR_SPARSE_THREADS": "4"} if method == "LHRR_SPARSE" else {}
    lists = []
    for threads in (1, 4):
        work = tmp_path / str(threads)
        config = sparse_config(data, method, work, **(extra if threads == 4 else {}))
        proc = run_sparse(sparse_dir, binary, config, work, threads=threads)
        assert proc.returncode == 0, proc.stdout
        lists.append(np.loadtxt(work / "out.txt", dtype=np.int64))
    assert np.array_equal(*lists)


def test_output_path_is_used_as_given(sparse_dir, data, tmp_path):
    """OUTPUT_FILE_PATH is the file itself (UDLF 1.70 appends .txt), parents are
    created, each line has exactly L ids, and a copy is always written to
    output/reranked_lists.txt in the working directory."""
    work = tmp_path / "work"
    config = base_config(data, "CPRR_SPARSE", sparse_params("CPRR_SPARSE"),
                         tmp_path / "nested" / "lists.txt", work / "log.txt")
    proc = run_sparse(sparse_dir, "udlf", config, work)
    assert proc.returncode == 0, proc.stdout

    lists = np.loadtxt(tmp_path / "nested" / "lists.txt", dtype=np.int64)
    assert lists.shape == (N, 100)
    assert not (tmp_path / "nested" / "lists.txt.txt").exists()
    assert np.array_equal(np.loadtxt(work / "output" / "reranked_lists.txt", dtype=np.int64),
                          lists)


def test_log_has_before_after_and_gains_in_percent(sparse_dir, data, tmp_path):
    proc = run_sparse(sparse_dir, "udlf", sparse_config(data, "CPRR_SPARSE", tmp_path),
                      tmp_path)
    assert proc.returncode == 0
    log = (tmp_path / "log.txt").read_text()
    assert "EFFECTIVENESS BEFORE RERANKING" in log
    assert "EFFECTIVENESS AFTER RERANKING" in log
    assert "- RELATIVE GAINS -" in log
    assert " MAP\t54.7131" in log and " MAP\t76.0246" in log     # x100
    assert " P@10\t83.15%" in log


def test_missing_keys_take_defaults(sparse_dir, data, tmp_path):
    """Only the essentials: absent keys (evaluation, output format...) get defaults."""
    config = "".join(f"{key} = {value}\n" for key, value in {
        "UDL_METHOD": "CPRR_SPARSE", "SIZE_DATASET": N, "INPUT_FILE_FORMAT": "RK",
        "INPUT_FILE": data["rk_num"], "INPUT_FILE_LIST": data["lists"],
        "INPUT_FILE_CLASSES": data["classes"], "OUTPUT_FILE_PATH": tmp_path / "out.txt",
        "OUTPUT_LOG_FILE_PATH": tmp_path / "log.txt", "PARAM_CPRR_SPARSE_L": 100,
        "PARAM_CPRR_SPARSE_K": 10}.items())
    proc = run_sparse(sparse_dir, "udlf", config, tmp_path)
    assert proc.returncode == 0, proc.stdout
    assert np.loadtxt(tmp_path / "out.txt", dtype=np.int64).shape == (N, 100)


def test_unknown_keys_are_reported_and_ignored(sparse_dir, data, tmp_path):
    config = sparse_config(data, "CPRR_SPARSE", tmp_path, PARAM_CPRR_SPARSE_X="1")
    proc = run_sparse(sparse_dir, "udlf", config, tmp_path)
    assert proc.returncode == 0
    assert "Unknown param PARAM_CPRR_SPARSE_X" in proc.stderr


def test_missing_config_exits_with_error(sparse_dir, tmp_path):
    """The answer pyUDLF uses to tell Sparse UDLF from UDLF 1.70."""
    proc = subprocess.run([str(sparse_dir / "udlf"), str(tmp_path / "missing.ini")],
                          capture_output=True, text=True)
    assert proc.returncode == 1
    assert "Error: Failed to open file:" in proc.stderr


def test_udlf_tmpdir_sets_the_scratch_directory(sparse_dir, data, tmp_path):
    scratch = tmp_path / "scratch"
    proc = run_sparse(sparse_dir, "udlf", sparse_config(data, "CPRR_SPARSE", tmp_path / "w"),
                      tmp_path / "w", env={"UDLF_TMPDIR": str(scratch)})
    assert proc.returncode == 0, proc.stdout
    assert scratch.is_dir()
