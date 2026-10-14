"""
The documentation must stay correct: the examples run, and the outputs
written in their comments are the real ones.

- examples/quickstart.py runs and prints what its comments say;
- the Python blocks of README.md and READMEpt.md run in sequence (like a
  notebook, starting from the quickstart), and every line
  `print(...)  # expected output` prints the expected output.
"""

import contextlib
import io
import os
import re
import subprocess
import sys
from pathlib import Path

import numpy as np
import pytest

import pyUDLF
from pyUDLF import UDLF

REPO = Path(__file__).resolve().parent.parent
QUICKSTART = REPO / "examples" / "quickstart.py"
READMES = ["README.md", "READMEpt.md"]
EXPECTED = re.compile(r"^\s*print\(.*\)\s+#\s*(.+)$")


def python_blocks(path):
    return re.findall(r"```python\n(.*?)```", path.read_text(), re.S)


def expected_outputs(code):
    return [m.group(1).strip() for line in code.splitlines() if (m := EXPECTED.match(line))]


CSR_BIN = Path(os.environ.get("UDLF_CSR_BIN") or
               REPO / ".udlf" / "UDLF-CSR" / "Source" / "bin" / "udlf")


@pytest.fixture(autouse=True)
def binary(udlf_bin, monkeypatch):
    from pyUDLF import run_calls
    monkeypatch.setenv("UDLF_BIN", str(udlf_bin))
    monkeypatch.setattr(run_calls, "bin_path", str(udlf_bin))
    if CSR_BIN.is_file():
        monkeypatch.setenv("UDLF_CSR_BIN", str(CSR_BIN))


def test_quickstart_example_prints_what_it_says(tmp_path):
    env = dict(os.environ, PYTHONPATH=str(Path(pyUDLF.__file__).resolve().parent.parent))
    proc = subprocess.run([sys.executable, str(QUICKSTART)], capture_output=True, text=True,
                          cwd=tmp_path, env=env)

    assert proc.returncode == 0, proc.stderr
    expected = expected_outputs(QUICKSTART.read_text())
    assert len(expected) == 3
    assert proc.stdout.splitlines() == expected


@pytest.mark.parametrize("readme", READMES)
def test_readme_quickstart_is_the_example_file(readme):
    assert python_blocks(REPO / readme)[0] == QUICKSTART.read_text()


def _write_dataset_files(namespace, directory):
    """Files the README examples refer to, from the quickstart data."""
    labels, ranked_lists = namespace["labels"], namespace["ranked_lists"]
    np.savetxt(directory / "ranked_lists.txt", ranked_lists, fmt="%d")
    (directory / "lists.txt").write_text("".join(f"{i}\n" for i in range(len(labels))))
    (directory / "classes.txt").write_text(
        "".join(f"{i}:{label}\n" for i, label in enumerate(labels)))
    (directory / "config.ini").write_text(
        "UDL_TASK = UDL\nUDL_METHOD = CPRR\nSIZE_DATASET = 200\n"
        "INPUT_FILE_FORMAT = RK\nINPUT_RK_FORMAT = NUM\nINPUT_FILE = ranked_lists.txt\n"
        "INPUT_FILE_LIST = lists.txt\nINPUT_FILE_CLASSES = classes.txt\n"
        "OUTPUT_FILE = TRUE\nOUTPUT_FILE_FORMAT = RK\nOUTPUT_RK_FORMAT = NUM\n"
        "OUTPUT_FILE_PATH = config_output\nOUTPUT_LOG_FILE_PATH = config_log.txt\n"
        "PARAM_CPRR_L = 100\nPARAM_CPRR_K = 10\nPARAM_CPRR_T = 2\n")


@pytest.mark.parametrize("readme", READMES)
def test_readme_examples_run_and_print_what_they_say(readme, tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    blocks = python_blocks(REPO / readme)
    namespace, output = {}, io.StringIO()

    with contextlib.redirect_stdout(output):
        exec(compile(blocks[0], f"{readme} (quickstart)", "exec"), namespace)
        _write_dataset_files(namespace, tmp_path)
        for i, code in enumerate(blocks[1:], 1):
            if 'backend="csr"' in code and not CSR_BIN.is_file():
                continue  # UDLF-CSR is not built (e.g. Windows / macOS)
            exec(compile(code, f"{readme} (block {i})", "exec"), namespace)

    printed = output.getvalue()
    for code in blocks:
        if 'backend="csr"' in code and not CSR_BIN.is_file():
            continue
        for expected in expected_outputs(code):
            assert expected in printed, f"{readme}: expected {expected!r}"


@pytest.mark.parametrize("readme", READMES)
def test_readme_shows_the_real_describe_output(readme):
    text = (REPO / readme).read_text()
    shown = "\n".join(f"# {line}" for line in UDLF.describe("CPRR").splitlines())
    assert shown in text
