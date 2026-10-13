"""
pyUDLF logs with the standard logging module and installs no handlers:
warnings and errors are shown by default, informative messages are not,
and an application that configures logging gets each message once.

Each scenario runs in a fresh interpreter, since logging state is global.
"""

import logging
import os
import subprocess
import sys
from pathlib import Path

import pytest

import pyUDLF
from conftest import METHOD_CASES

PACKAGE_PARENT = str(Path(pyUDLF.__file__).resolve().parent.parent)
TESTS_DIR = str(Path(__file__).resolve().parent)

RUN_LEGACY = """
import sys
sys.path.insert(0, {tests!r})
from conftest import make_input, METHOD_CASES
from pyUDLF import run_calls
from pathlib import Path
run_calls.bin_path = {bin!r}
data = {data!r}
tmp = Path({tmp!r})
inp = make_input({template!r}, data, "CPRR", METHOD_CASES["CPRR"], tmp / "out", tmp / "log.txt")
inp.set_param("PARAM_CPRR_K", {k})
result = run_calls.run(inp, get_output=True)
print("RESULT", bool(result))
"""


def _run(code, tmp_path):
    env = dict(os.environ, PYTHONPATH=PACKAGE_PARENT)
    return subprocess.run([sys.executable, "-c", code], capture_output=True, text=True,
                          env=env, cwd=tmp_path)


def _legacy_script(udlf_bin, udlf_template, data, tmp_path, k=10, setup=""):
    return setup + RUN_LEGACY.format(tests=TESTS_DIR, bin=str(udlf_bin), data=data,
                                     tmp=str(tmp_path), template=str(udlf_template), k=k)


def test_successful_run_is_quiet_by_default(udlf_bin, udlf_template, data, tmp_path):
    proc = _run(_legacy_script(udlf_bin, udlf_template, data, tmp_path), tmp_path)

    assert proc.stdout == "RESULT True\n"
    assert proc.stderr == ""


def test_errors_are_shown_by_default(udlf_bin, udlf_template, data, tmp_path):
    proc = _run(_legacy_script(udlf_bin, udlf_template, data, tmp_path, k=150), tmp_path)

    assert proc.stdout == "RESULT False\n"
    assert "UDLF exited with code 1" in proc.stderr
    assert "K can't be greater than L" in proc.stderr


def test_enable_logging_shows_informative_messages(udlf_bin, udlf_template, data, tmp_path):
    setup = "import pyUDLF\npyUDLF.enable_logging('INFO')\n"
    proc = _run(_legacy_script(udlf_bin, udlf_template, data, tmp_path, setup=setup),
                tmp_path)

    assert "[INFO] UDLF run successfully." in proc.stderr


def test_application_logging_gets_each_message_once(udlf_bin, udlf_template, data,
                                                    tmp_path):
    setup = ("import logging\n"
             "logging.basicConfig(level=logging.INFO, format='%(name)s|%(message)s')\n")
    proc = _run(_legacy_script(udlf_bin, udlf_template, data, tmp_path, setup=setup),
                tmp_path)

    lines = proc.stderr.splitlines()
    assert lines.count("pyUDLF.run_calls|UDLF run successfully.") == 1


def test_no_handlers_are_installed():
    import pyUDLF.utils.gridSearch  # noqa: F401  (import every module)
    import pyUDLF.utils.inputType  # noqa: F401
    loggers = [logging.getLogger(name) for name in logging.root.manager.loggerDict
               if name.startswith("pyUDLF")]

    assert loggers
    assert all(not logger.handlers for logger in loggers)


def test_readers_do_not_print(data, capsys):
    from pyUDLF.utils import readData

    readData.read_ranked_lists_file_numeric(data["rk_num"], top_k=5)
    readData.read_ranked_lists_file_string(data["rk_str"], top_k=5)
    readData.read_matrix_file(data["matrix_dist"])

    assert capsys.readouterr() == ("", "")
