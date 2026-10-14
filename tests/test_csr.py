"""
UDLF-CSR backend (pyUDLF.UDLF(backend="csr") and pyUDLF.csr).

The runs through pyUDLF are compared with UDLF-CSR executed directly on a
config written by hand. Needs the UDLF-CSR binary (scripts/build_csr.sh builds
the dense and sparse engines); otherwise these tests are skipped.

Everything runs with one thread: with several threads, the dense engines of
UDLF-CSR (commit b391800) give slightly different results from run to run.
"""

import os
import random
import subprocess
from pathlib import Path

import numpy as np
import pytest

from conftest import N
from pyUDLF import UDLF, UDLFNotFoundError, UDLFParamError, UDLFRunError, csr

# Engines compared with direct runs. scripts/build_csr.sh builds dense and sparse;
# with a full build (--full) set PYUDLF_CSR_ENGINES=dense,sparse,mkl,blas,eigen
ENGINES = os.environ.get("PYUDLF_CSR_ENGINES", "dense,sparse").replace(" ", "").split(",")
CASES = [(method, engine, csr.method_name(method, engine)[1])
         for method in csr.METHODS for engine in ENGINES]
PARAMS = {"l": 100, "k": 10, "t": 2}


@pytest.fixture
def backend(csr_bin):
    return UDLF(bin_path=str(csr_bin), backend="csr", threads=1)


@pytest.fixture(scope="session")
def rks(data):
    return np.loadtxt(data["rk_num"], dtype=np.int64)


@pytest.fixture(scope="session")
def labels(data):
    return [token.split(":")[1] for token in Path(data["classes"]).read_text().split()]


def csr_config(data, csr_method, workdir, input_file=None, matrix_path="/dev/null"):
    """Every variable UDLF-CSR needs, written by hand."""
    values = {
        "UDL_TASK": "UDL", "UDL_METHOD": csr_method, "SIZE_DATASET": N,
        "INPUT_FILE_FORMAT": "RK", "INPUT_MATRIX_TYPE": "DIST", "INPUT_RK_FORMAT": "NUM",
        "MATRIX_TO_RK_SORTING": "HEAP", "NUM_INPUT_FUSION_FILES": 0,
        "INPUT_FILE": input_file or data["rk_num"], "INPUT_FILE_LIST": data["lists"],
        "INPUT_FILE_CLASSES": data["classes"], "INPUT_IMAGES_PATH": "images/",
        "OUTPUT_FILE": "TRUE", "OUTPUT_FILE_FORMAT": "RK", "OUTPUT_MATRIX_TYPE": "DIST",
        "OUTPUT_RK_FORMAT": "NUM", "OUTPUT_FILE_PATH": matrix_path,
        "OUTPUT_HTML_RK_PER_FILE": 1, "OUTPUT_HTML_RK_SIZE": 20,
        "OUTPUT_HTML_RK_COLORS": "TRUE", "OUTPUT_HTML_RK_BEFORE_AFTER": "TRUE",
        "OUTPUT_LOG_FILE_PATH": str(Path(workdir) / "log.txt"),
        "EFFICIENCY_EVAL": "TRUE", "EFFECTIVENESS_EVAL": "TRUE",
        "EFFECTIVENESS_COMPUTE_PRECISIONS": "TRUE", "EFFECTIVENESS_COMPUTE_MAP": "TRUE",
        "EFFECTIVENESS_COMPUTE_RECALL": "TRUE",
        "EFFECTIVENESS_RECALLS_TO_COMPUTE": "5,10", "EFFECTIVENESS_PRECISIONS_TO_COMPUTE": "5,10",
    }
    values.update({f"PARAM_{csr_method}_{key.upper()}": value for key, value in PARAMS.items()})
    return "".join(f"{key} = {value}\n" for key, value in values.items())


def run_csr_direct(csr_bin, data, workdir, csr_method, **kwargs):
    workdir = Path(workdir)
    (workdir / "output").mkdir(parents=True, exist_ok=True)
    cfg = workdir / "direct.ini"
    cfg.write_text(csr_config(data, csr_method, workdir, **kwargs))
    env = dict(os.environ, OMP_NUM_THREADS="1")
    for _ in range(3):  # intermittent UDLF-CSR startup error, see csr.TRANSIENT_ERROR
        proc = subprocess.run([str(csr_bin), str(cfg)], capture_output=True, text=True,
                              cwd=workdir, env=env)
        if csr.TRANSIENT_ERROR not in proc.stdout + proc.stderr:
            break
    assert "Error" not in proc.stdout + proc.stderr, proc.stdout + proc.stderr
    lists = np.loadtxt(workdir / "output" / "reranked_lists.txt", dtype=np.int64)
    return lists, csr.parse_log((workdir / "log.txt").read_text())


# --------------------------------------------------------------------------
# pyUDLF.csr helpers
# --------------------------------------------------------------------------

@pytest.mark.parametrize("method, engine, expected", [
    ("CPRR", None, ("CPRR", "CPRR")),
    ("cprr", "sparse", ("CPRR", "CPRR_SPARSE")),
    ("LHRR_MKL", None, ("LHRR", "LHRR_MKL")),
    ("LHRR_MKL", "mkl", ("LHRR", "LHRR_MKL")),
    ("CPRR", "Eigen", ("CPRR", "CPRR_EIGEN")),
])
def test_method_name(method, engine, expected):
    assert csr.method_name(method, engine) == expected


@pytest.mark.parametrize("method, engine", [("RDPAC", None), ("CPRR_GPU", None),
                                            ("CPRR", "cuda"), ("CPRR_SPARSE", "mkl")])
def test_method_name_rejects(method, engine):
    with pytest.raises(ValueError):
        csr.method_name(method, engine)


def test_check_output_finds_errors_despite_exit_code_zero():
    output = ("Running Method: CPRR\nAvailable Methods in Registry: CPRR CPRR_SPARSE \n"
              "Execution Error: K > L\nExecution Completed!\n")
    assert csr.check_output(output) == ["UDLF-CSR: K > L"]
    assert csr.check_output("Running Method: CPRR\nExecution Completed!\n") == []


def test_parse_log_converts_percentages():
    log = ("\n\nEFFECTIVENESS\n\n P@5\t76.1%\n Recall@5\t19.025%\n MAP\t54.7131\n"
           "\n\nEFFECTIVENESS\n\n P@5\t85.6%\n Recall@5\t21.4%\n MAP\t76.3318\n")
    parsed = csr.parse_log(log)
    assert parsed["before"] == pytest.approx({"P@5": 0.761, "Recall@5": 0.19025, "MAP": 0.547131})
    assert parsed["after"]["MAP"] == pytest.approx(0.763318)


# --------------------------------------------------------------------------
# Same results as UDLF-CSR run directly
# --------------------------------------------------------------------------

@pytest.mark.parametrize("method, engine, csr_method", CASES)
def test_run_matches_direct_run(backend, csr_bin, data, tmp_path, rks, labels,
                                method, engine, csr_method):
    res = backend.run(method, ranked_lists=rks, params=PARAMS, classes=labels,
                      engine=engine, precisions=[5, 10], recalls=[5, 10])

    lists, raw = run_csr_direct(csr_bin, data, tmp_path / "direct", csr_method)
    np.testing.assert_array_equal(res.ranked_lists, lists[:, :PARAMS["l"]])
    assert res.method == csr_method
    # measures recomputed in Python agree with UDLF-CSR on this balanced dataset
    for section in ("before", "after"):
        assert res.raw_metrics[section] == pytest.approx(raw[section])
        assert res.metrics[section] == pytest.approx(raw[section], abs=1.5e-4)


def test_csr_name_or_engine_give_the_same_run(backend, rks, labels):
    by_engine = backend.run("CPRR", engine="sparse", ranked_lists=rks, params=PARAMS)
    by_name = backend.run("CPRR_SPARSE", ranked_lists=rks, params=PARAMS)
    np.testing.assert_array_equal(by_engine.ranked_lists, by_name.ranked_lists)


def test_before_measures_match_the_udlf_backend(backend, udlf_bin, rks, labels):
    """Both backends evaluate the input the same way (UDLF definitions)."""
    original = UDLF(bin_path=str(udlf_bin)).run("CPRR", ranked_lists=rks, params=PARAMS,
                                                classes=labels)
    res = backend.run("CPRR", ranked_lists=rks, params=PARAMS, classes=labels)

    # UDLF rounds float32 values; allow one unit in the 4th decimal
    assert res.metrics["before"] == pytest.approx(original.metrics["before"], abs=1.5e-4)


def test_per_query_reproduces_the_metrics(backend, rks, labels):
    res = backend.run("LHRR", ranked_lists=rks, params=PARAMS, classes=labels)
    before, after = res.per_query()
    assert before.mean() == pytest.approx(res.map_before, abs=1e-4)
    assert after.mean() == pytest.approx(res.map_after, abs=1e-4)


def test_repeated_elements_are_reported(backend, rks, labels, caplog):
    dense = backend.run("CPRR", ranked_lists=rks, params=PARAMS, classes=labels)
    sparse = backend.run("CPRR", ranked_lists=rks, params=PARAMS, classes=labels,
                         engine="sparse")

    def repeated(result):  # (a run may also warn that it was run again)
        return [w for w in result.warnings if "repeated elements" in w]

    assert repeated(dense) == []
    rows_with_repetitions = sum(len(set(row)) < len(row) for row in sparse.ranked_lists)
    assert rows_with_repetitions > 0  # UDLF-CSR b391800, see the CHANGELOG
    assert len(repeated(sparse)) == 1
    assert f"{rows_with_repetitions} of {N} ranked lists" in repeated(sparse)[0]
    assert "repeated elements" in caplog.text


def test_matrix_output(backend, csr_bin, data, tmp_path, rks):
    res = backend.run("CPRR", ranked_lists=rks, params=PARAMS, output="matrix")

    matrix_file = tmp_path / "direct" / "matrix.txt"
    run_csr_direct(csr_bin, data, tmp_path / "direct", "CPRR", matrix_path=str(matrix_file))
    np.testing.assert_array_equal(res.matrix, np.loadtxt(matrix_file))
    assert res.ranked_lists is None and res.matrix.shape == (N, N)


def test_without_classes(backend, rks):
    res = backend.run("CPRR", ranked_lists=rks, params=PARAMS)
    assert res.metrics == {} and res.raw_metrics == {}
    assert res.ranked_lists.shape == (N, PARAMS["l"])


def test_classes_file_in_another_order(backend, data, tmp_path, rks, labels):
    """UDLF-CSR reads classes by line order; pyUDLF matches them by name."""
    lines = Path(data["classes"]).read_text().splitlines()
    random.Random(0).shuffle(lines)
    shuffled = tmp_path / "classes_shuffled.txt"
    shuffled.write_text("\n".join(lines) + "\n")

    from_file = backend.run("CPRR", ranked_lists=rks, params=PARAMS, classes=str(shuffled),
                            names=data["lists"])
    from_labels = backend.run("CPRR", ranked_lists=rks, params=PARAMS, classes=labels)

    assert from_file.metrics == from_labels.metrics
    assert from_file.raw_metrics == from_labels.raw_metrics


def test_files_are_kept_on_request(backend, rks, labels):
    res = backend.run("CPRR", ranked_lists=rks, params=PARAMS, classes=labels,
                      keep_files=True)
    assert set(res.files) == {"config", "log", "lists", "classes", "output"}
    assert all(Path(p).is_file() for p in res.files.values())


def test_no_temporary_files_are_left(backend, rks, tmp_path):
    backend.run("CPRR", ranked_lists=rks, params=PARAMS)
    assert not list(tmp_path.glob("pyudlf_*"))  # tempfile is redirected to tmp_path


# --------------------------------------------------------------------------
# run_config
# --------------------------------------------------------------------------

def test_run_config(backend, csr_bin, data, tmp_path, monkeypatch):
    user = tmp_path / "user"
    user.mkdir()
    cfg = user / "config.ini"
    cfg.write_text(csr_config(data, "CPRR_SPARSE", user))
    monkeypatch.chdir(user)

    res = backend.run_config(cfg)

    lists, raw = run_csr_direct(csr_bin, data, tmp_path / "direct", "CPRR_SPARSE")
    np.testing.assert_array_equal(res.ranked_lists, lists[:, :PARAMS["l"]])
    assert res.raw_metrics["after"] == pytest.approx(raw["after"])
    assert (user / "output" / "reranked_lists.txt").is_file()  # created by pyUDLF
    assert res.map_after == pytest.approx(raw["after"]["MAP"], abs=1.5e-4)


def test_run_config_warns_about_classes_order(backend, data, tmp_path, monkeypatch):
    lines = Path(data["classes"]).read_text().splitlines()
    random.Random(1).shuffle(lines)  # (reversing would only rename the classes)
    shuffled = tmp_path / "classes_shuffled.txt"
    shuffled.write_text("\n".join(lines) + "\n")
    cfg = tmp_path / "config.ini"
    cfg.write_text(csr_config(data, "CPRR", tmp_path).replace(
        f"INPUT_FILE_CLASSES = {data['classes']}", f"INPUT_FILE_CLASSES = {shuffled}"))
    monkeypatch.chdir(tmp_path)

    res = backend.run_config(cfg)

    assert any("not in the order of the lists file" in w for w in res.warnings)
    assert res.raw_metrics["after"]["MAP"] != pytest.approx(res.map_after, abs=1e-3)


# --------------------------------------------------------------------------
# Errors
# --------------------------------------------------------------------------

def test_backend_mismatch_is_detected(csr_bin, udlf_bin):
    with pytest.raises(UDLFParamError, match="UDLF-CSR binary"):
        UDLF(bin_path=str(csr_bin))
    with pytest.raises(UDLFParamError, match="is a UDLF binary"):
        UDLF(bin_path=str(udlf_bin), backend="csr")
    with pytest.raises(UDLFParamError, match="backend must be"):
        UDLF(bin_path=str(udlf_bin), backend="gpu")


def test_binary_from_environment(csr_bin, tmp_path, monkeypatch):
    monkeypatch.setenv("UDLF_CSR_BIN", str(csr_bin))
    assert UDLF(backend="csr").bin_path == str(csr_bin)
    monkeypatch.delenv("UDLF_CSR_BIN")
    with pytest.raises(UDLFNotFoundError, match="build_csr.sh"):
        UDLF(backend="csr")


@pytest.mark.parametrize("kwargs, error, message", [
    (dict(method="RDPAC"), UDLFParamError, "only"),
    (dict(engine="cuda"), UDLFParamError, "engine"),
    (dict(matrix=np.eye(N), ranked_lists=None), UDLFParamError, "only ranked lists"),
    (dict(params={"l": 100, "k": 150}), UDLFParamError, "larger than l"),
    (dict(params={"l": N + 1}), UDLFParamError, "larger than the dataset"),
    (dict(output="matrix", output_matrix_type="sim"), UDLFParamError, "distance"),
    (dict(engine="mkl"), UDLFRunError, "This UDLF-CSR build has only"),
])
def test_invalid_runs(backend, rks, kwargs, error, message):
    arguments = dict(dict(method="CPRR", ranked_lists=rks, params=PARAMS), **kwargs)
    with pytest.raises(error, match=message):
        backend.run(**arguments)


def test_input_shorter_than_l(backend, rks):
    with pytest.raises(UDLFParamError, match="reads 100 per line"):
        backend.run("CPRR", ranked_lists=rks[:, :50], params=PARAMS)


def test_string_ranked_lists_and_fusion_are_not_supported(backend, data, rks):
    with pytest.raises(UDLFParamError, match="indices"):
        backend.run("CPRR", ranked_lists=data["rk_str"], names=data["lists"], params=PARAMS)
    with pytest.raises(UDLFParamError, match="FUSION"):
        backend.fuse("CPRR", [rks, rks])


def test_engine_is_only_for_csr(udlf_bin, rks):
    with pytest.raises(UDLFParamError, match="backend='csr'"):
        UDLF(bin_path=str(udlf_bin)).run("CPRR", ranked_lists=rks, engine="sparse")


# --------------------------------------------------------------------------
# Threads and the intermittent startup error
# --------------------------------------------------------------------------

def test_one_thread_makes_dense_engines_reproducible(backend, rks):
    first = backend.run("LHRR", ranked_lists=rks, params=PARAMS)
    second = backend.run("LHRR", ranked_lists=rks, params=PARAMS)
    np.testing.assert_array_equal(first.ranked_lists, second.ranked_lists)


@pytest.mark.parametrize("threads", [0, -1, 1.5, True, "2"])
def test_invalid_threads(csr_bin, threads):
    with pytest.raises(UDLFParamError, match="threads"):
        UDLF(bin_path=str(csr_bin), backend="csr", threads=threads)


def test_transient_startup_error_is_retried(csr_bin, tmp_path, rks, caplog):
    """A wrapper binary that fails like UDLF-CSR's dangling pointer bug on its
    first run, then runs the real UDLF-CSR."""
    marker = tmp_path / "failed_once"
    fake = tmp_path / "flaky_udlf"
    fake.write_text(
        "#!/bin/sh\n"
        f'if [ -f "$1" ] && [ ! -f "{marker}" ]; then\n'
        f'  touch "{marker}"; echo "Error: Failed to open backing file"; exit 0\n'
        "fi\n"
        f'exec "{csr_bin}" "$@"\n')
    fake.chmod(0o755)

    res = UDLF(bin_path=str(fake), backend="csr", threads=1).run(
        "CPRR", ranked_lists=rks, params=PARAMS)

    assert marker.exists()
    assert any("was run again" in w for w in res.warnings)
    assert res.ranked_lists.shape == (N, PARAMS["l"])


def test_check_output_explains_the_transient_error():
    problems = csr.check_output("Error: Failed to open backing file\n")
    assert "intermittent UDLF-CSR bug" in problems[-1]
