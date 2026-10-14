"""Packaging checks: version metadata and optional dependencies."""

import os
import re
import subprocess
import sys
from pathlib import Path

import pyUDLF

PACKAGE_PARENT = str(Path(pyUDLF.__file__).resolve().parent.parent)


def _run_python(code):
    """Run code in a fresh interpreter that imports this same pyUDLF."""
    env = dict(os.environ, PYTHONPATH=PACKAGE_PARENT)
    return subprocess.run([sys.executable, "-c", code], capture_output=True,
                          text=True, env=env)


def test_version_is_pep440():
    assert re.fullmatch(r"\d+\.\d+\.\d+((a|b|rc)\d+)?(\.dev\d+)?", pyUDLF.__version__)


def test_imports_without_pillow():
    """Pillow is optional (extra "viz"): every module must import without it."""
    proc = _run_python(
        "import sys; sys.modules['PIL'] = None\n"  # makes 'import PIL' fail
        "import pyUDLF.run_calls, pyUDLF.utils.inputType, pyUDLF.utils.outputType\n"
        "import pyUDLF.utils.gridSearch, pyUDLF.utils.visualization\n"
    )
    assert proc.returncode == 0, proc.stderr


def test_visualization_without_pillow_explains_how_to_install():
    proc = _run_python(
        "import sys; sys.modules['PIL'] = None\n"
        "from pyUDLF.utils.visualization import render_ranked_list\n"
        "try:\n"
        "    render_ranked_list('rk', 'list', 'classes', 'images', line=0)\n"
        "except ImportError as e:\n"
        "    print(e)\n"
    )
    assert proc.returncode == 0, proc.stderr
    assert 'pip install "pyUDLF[viz]"' in proc.stdout
