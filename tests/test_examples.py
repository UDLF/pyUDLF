"""
Every script in examples/ must run and print its results.
"""

import os
import subprocess
import sys
from pathlib import Path

import numpy as np
import pytest

import pyUDLF

REPO = Path(__file__).resolve().parent.parent
EXAMPLES = REPO / "examples"
CSR_BIN = Path(os.environ.get("UDLF_CSR_BIN") or
               REPO / ".udlf" / "UDLF-CSR" / "Source" / "bin" / "udlf")

# script -> text its output must contain
EXPECTED = {
    "quickstart.py": "186 of 200 queries improved",
    "compare_methods.py": "RDPAC",
    "parameter_search.py": "Best: l = 150, k = 30",
    "input_formats.py": "similarity matrix      MAP 0.5471 -> 0.7602   (same lists)",
    "fusion.py": "Fused (CPRR): MAP",
    "per_query_analysis.py": "queries improved",
    "your_own_data.py": "MAP 0.5471 -> 0.7602",
    "csr_engines.py": "CSR sparse",
    "legacy_api.py": "Queries with the largest gain",
}


def run_example(script, tmp_path, udlf_bin, *args):
    env = dict(os.environ, UDLF_BIN=str(udlf_bin), TMPDIR=str(tmp_path), TEMP=str(tmp_path),
               PYTHONPATH=str(Path(pyUDLF.__file__).resolve().parent.parent))
    if CSR_BIN.is_file():
        env["UDLF_CSR_BIN"] = str(CSR_BIN)
    return subprocess.run([sys.executable, str(EXAMPLES / script), *args], capture_output=True,
                          text=True, cwd=tmp_path, env=env, timeout=600)


def test_every_example_is_tested():
    assert sorted(p.name for p in EXAMPLES.glob("*.py")) == sorted(EXPECTED)


@pytest.mark.parametrize("script", sorted(EXPECTED))
def test_example_runs(script, tmp_path, udlf_bin):
    if script == "csr_engines.py" and not CSR_BIN.is_file():
        pytest.skip("UDLF-CSR is not built (scripts/build_csr.sh)")
    proc = run_example(script, tmp_path, udlf_bin)

    assert proc.returncode == 0, proc.stderr
    assert EXPECTED[script] in proc.stdout, proc.stdout


def test_your_own_data_with_arguments(tmp_path, udlf_bin):
    """Features in a .npy file and labels in a text file, as a user would pass them."""
    rng = np.random.default_rng(0)
    labels = np.repeat(np.arange(5), 30)
    features = rng.normal(size=(5, 16))[labels] + rng.normal(scale=1.5, size=(150, 16))
    np.save(tmp_path / "features.npy", features)
    (tmp_path / "labels.txt").write_text("\n".join(map(str, labels)) + "\n")

    proc = run_example("your_own_data.py", tmp_path, udlf_bin,
                       "--features", "features.npy", "--classes-list", "labels.txt",
                       "--method", "LHRR", "--param", "l=60", "--param", "k=8",
                       "--output", "reranked.txt")

    assert proc.returncode == 0, proc.stderr
    assert "Result(method='LHRR', ranked_lists=(150, 60)" in proc.stdout
    assert np.loadtxt(tmp_path / "reranked.txt", dtype=int).shape == (150, 60)
