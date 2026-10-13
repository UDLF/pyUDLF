"""
Shared fixtures for the pyUDLF test suite.

The tests run the real UDLF binary. It is looked up in this order:
  1. the ``UDLF_BIN`` environment variable;
  2. ``.udlf/UDLF/bin/udlf`` inside the repository (created by
     ``scripts/build_udlf.sh``).
If no binary is found, tests that need it are skipped.

The UDLF reference ``config.ini`` (used by ``InputType`` as a template) is
looked up next to the binary, or in the ``UDLF_CONFIG`` environment variable.
"""

import os
import re
import subprocess
import tempfile
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = Path(__file__).resolve().parent / "data" / "synthetic"
N = 200

# Small evaluation depths: every method below outputs ranked lists of size >= 50.
PRECISIONS = "5,10,20"
RECALLS = "5,10,20"

# Method parameters suitable for the synthetic dataset (N = 200).
# Keys are the full UDLF parameter names, values exactly as written in a config.
METHOD_CASES = {
    "NONE": {"PARAM_NONE_L": "100"},
    "CPRR": {"PARAM_CPRR_L": "100", "PARAM_CPRR_K": "10", "PARAM_CPRR_T": "2"},
    "RLRECOM": {"PARAM_RLRECOM_L": "100", "PARAM_RLRECOM_K": "8",
                "PARAM_RLRECOM_LAMBDA": "2.0", "PARAM_RLRECOM_EPSILON": "0.0125"},
    "RLSIM": {"PARAM_RLSIM_TOPK": "10", "PARAM_RLSIM_CK": "100", "PARAM_RLSIM_T": "3",
              "PARAM_RLSIM_METRIC": "INTERSECTION"},
    "CONTEXTRR": {"PARAM_CONTEXTRR_L": "25", "PARAM_CONTEXTRR_K": "7",
                  "PARAM_CONTEXTRR_T": "5", "PARAM_CONTEXTRR_NBYK": "1",
                  "PARAM_CONTEXTRR_OPTIMIZATIONS": "TRUE"},
    "RECKNNGRAPH": {"PARAM_RECKNNGRAPH_L": "100", "PARAM_RECKNNGRAPH_K": "10",
                    "PARAM_RECKNNGRAPH_EPSILON": "0.0125"},
    "RKGRAPH": {"PARAM_RKGRAPH_K": "10", "PARAM_RKGRAPH_T": "1",
                "PARAM_RKGRAPH_P": "0.95", "PARAM_RKGRAPH_L": "100"},
    "CORGRAPH": {"PARAM_CORGRAPH_L": "100", "PARAM_CORGRAPH_K": "10",
                 "PARAM_CORGRAPH_THRESHOLD_START": "0.35",
                 "PARAM_CORGRAPH_THRESHOLD_END": "1.0",
                 "PARAM_CORGRAPH_THRESHOLD_INC": "0.005",
                 "PARAM_CORGRAPH_CORRELATION": "PEARSON"},
    "LHRR": {"PARAM_LHRR_K": "10", "PARAM_LHRR_L": "100", "PARAM_LHRR_T": "2"},
    "BFSTREE": {"PARAM_BFSTREE_L": "100", "PARAM_BFSTREE_K": "10",
                "PARAM_BFSTREE_CORRELATION_METRIC": "RBO"},
    "RDPAC": {"PARAM_RDPAC_K_END": "10", "PARAM_RDPAC_K_INC": "1",
              "PARAM_RDPAC_K_START": "1", "PARAM_RDPAC_L": "50",
              "PARAM_RDPAC_L_MULT": "2", "PARAM_RDPAC_P": "0.6", "PARAM_RDPAC_PL": "0.99"},
    "RFE": {"PARAM_RFE_K": "10", "PARAM_RFE_T": "2", "PARAM_RFE_L": "100",
            "PARAM_RFE_PA": "0.1", "PARAM_RFE_TH_CC": "0",
            "PARAM_RFE_RERANK_BY_EMB": "FALSE", "PARAM_RFE_EXPORT_EMBEDDINGS": "FALSE",
            "PARAM_RFE_PERFORM_CCS": "FALSE",
            # UDLF aborts if these two are not declared (relative to the test cwd)
            "PARAM_RFE_EMBEDDINGS_PATH": "embeddings.txt",
            "PARAM_RFE_CCS_PATH": "ccs.txt"},
}


def _find_binary():
    env = os.environ.get("UDLF_BIN")
    if env:
        return Path(env).expanduser()
    return REPO_ROOT / ".udlf" / "UDLF" / "bin" / "udlf"


@pytest.fixture(scope="session")
def udlf_bin():
    path = _find_binary()
    if not path.is_file():
        pytest.skip(f"UDLF binary not found at {path}. Run scripts/build_udlf.sh "
                    "or set UDLF_BIN.")
    return path


@pytest.fixture(scope="session")
def udlf_template(udlf_bin):
    env = os.environ.get("UDLF_CONFIG")
    path = Path(env).expanduser() if env else udlf_bin.parent / "config.ini"
    if not path.is_file():
        pytest.skip(f"UDLF reference config.ini not found at {path}. Set UDLF_CONFIG.")
    return path


@pytest.fixture(scope="session")
def data():
    """Paths to the synthetic dataset files (as strings)."""
    names = ["lists", "classes", "classes_str", "rk_num", "rk_str",
             "matrix_dist", "matrix_sim"]
    return {name: str(DATA_DIR / f"{name}.txt") for name in names}


@pytest.fixture(autouse=True)
def isolate_tmp(tmp_path, monkeypatch):
    """Keep every temporary file of a test (configs, logs, UDLF side files)
    inside the test's own tmp_path, and run from there."""
    monkeypatch.setattr(tempfile, "tempdir", str(tmp_path))
    monkeypatch.chdir(tmp_path)


@pytest.fixture
def old_api(udlf_bin, monkeypatch):
    """The legacy API (run_calls + InputType) pointed at the test binary."""
    from pyUDLF import run_calls
    monkeypatch.setattr(run_calls, "bin_path", str(udlf_bin))
    return run_calls


def base_config(data, method, params, out_base, log_path, input_file=None,
                input_format="RK", rk_format="NUM", matrix_type="DIST"):
    """Minimal UDLF config, written by hand (independent of the wrapper)."""
    lines = {
        "UDL_TASK": "UDL",
        "UDL_METHOD": method,
        "SIZE_DATASET": str(N),
        "INPUT_FILE_FORMAT": input_format,
        "INPUT_RK_FORMAT": rk_format,
        "INPUT_MATRIX_TYPE": matrix_type,
        "INPUT_FILE": input_file or data["rk_num"],
        "INPUT_FILE_LIST": data["lists"],
        "INPUT_FILE_CLASSES": data["classes"],
        "OUTPUT_FILE": "TRUE",
        "OUTPUT_FILE_FORMAT": "RK",
        "OUTPUT_RK_FORMAT": "NUM",
        "OUTPUT_FILE_PATH": str(out_base),
        "OUTPUT_LOG_FILE_PATH": str(log_path),
        "EFFECTIVENESS_EVAL": "TRUE",
        "EFFECTIVENESS_PRECISIONS_TO_COMPUTE": PRECISIONS,
        "EFFECTIVENESS_RECALLS_TO_COMPUTE": RECALLS,
    }
    lines.update(params)
    return "".join(f"{k} = {v}\n" for k, v in lines.items())


def run_direct(udlf_bin, config_text, workdir):
    """Run the UDLF binary directly on a config written by hand."""
    cfg = Path(workdir) / "direct_config.ini"
    cfg.write_text(config_text)
    proc = subprocess.run([str(udlf_bin), str(cfg)], capture_output=True, text=True,
                          cwd=workdir)
    return proc


def parse_map(log_path):
    """Return (map_before, map_after) as written in a UDLF log file."""
    values = re.findall(r"^\s*MAP\s+([0-9.]+)\s*$", Path(log_path).read_text(), re.M)
    return float(values[0]), float(values[1])


def make_input(udlf_template, data, method, params, out_base, log_path,
               input_file=None, input_format="RK", rk_format="NUM",
               matrix_type="DIST"):
    """Build a legacy InputType equivalent to ``base_config``."""
    from pyUDLF.utils.inputType import InputType

    inp = InputType(config_path=str(udlf_template))
    inp.set_task("UDL")
    inp.set_method_name(method)
    inp.set_dataset_size(N)
    inp.set_input_file_format(input_format)
    inp.set_rk_format(rk_format)
    inp.set_input_matrix_type(matrix_type)
    inp.set_input_file(input_file or data["rk_num"])
    inp.set_lists_file(data["lists"])
    inp.set_classes_file(data["classes"])
    inp.set_output_file(True)
    inp.set_output_file_format("RK")
    inp.set_output_rk_format("NUM")
    inp.set_output_file_path(str(out_base))
    inp.set_output_log_file_path(str(log_path))
    inp.set_effectiveness_eval(True)
    inp.set_effectiveness_precisions_to_compute([int(x) for x in PRECISIONS.split(",")])
    inp.set_effectiveness_recalls_to_compute([int(x) for x in RECALLS.split(",")])
    for key, value in params.items():
        inp.set_param(key, value)
    return inp
