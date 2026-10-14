"""
Compare UDLF with the engines of UDLF-CSR on the same input.

    python examples/csr_engines.py --csr-bin path/to/UDLF-CSR/Source/bin/udlf

(or set the UDLF_CSR_BIN environment variable; scripts/build_csr.sh builds
UDLF-CSR into .udlf/UDLF-CSR, which is used when present).

Uses the synthetic dataset of the repository (200 elements, 10 classes).
Measures are computed by pyUDLF with the UDLF definitions, so all rows are
comparable; res.warnings reports problems found in the results.
"""

import argparse
import logging
import os
from pathlib import Path

import numpy as np

from pyUDLF import UDLF, UDLFRunError

REPO = Path(__file__).resolve().parent.parent
DATA = REPO / "tests" / "data" / "synthetic"
BUILT = REPO / ".udlf" / "UDLF-CSR" / "Source" / "bin" / "udlf"

parser = argparse.ArgumentParser(description="Compare UDLF with the UDLF-CSR engines.")
parser.add_argument("--csr-bin", default=os.environ.get("UDLF_CSR_BIN") or (BUILT if BUILT.is_file() else None))
parser.add_argument("--engines", default="dense,sparse,mkl,blas,eigen")
args = parser.parse_args()
if not args.csr_bin:
    raise SystemExit("UDLF-CSR binary not found: build it with scripts/build_csr.sh, "
                     "or pass --csr-bin / set UDLF_CSR_BIN.")

rks = np.loadtxt(DATA / "rk_num.txt", dtype=int)
labels = [token.split(":")[1] for token in (DATA / "classes.txt").read_text().split()]
params = {"l": 100, "k": 10}

# The repeated-elements warning is summarized in the table below (from the results)
logging.getLogger("pyUDLF").setLevel(logging.ERROR)

udlf = UDLF()
csr = UDLF(bin_path=args.csr_bin, backend="csr", threads=1)   # threads=1: reproducible

for method in ["CPRR", "LHRR"]:
    reference = udlf.run(method, ranked_lists=rks, params=params, classes=labels)
    print(f"{method} (l=100, k=10)")
    print(f"  {'UDLF 1.70':14s} MAP {reference.map_before:.4f} -> {reference.map_after:.4f}")
    for engine in args.engines.split(","):
        try:
            res = csr.run(method, ranked_lists=rks, params=params, classes=labels, engine=engine)
        except UDLFRunError:
            print(f"  {'CSR ' + engine:14s} not available in this UDLF-CSR build")
            continue
        repeated = sum(len(set(row)) < len(row) for row in res.ranked_lists)
        note = f"  ({repeated} lists with repeated elements)" if repeated else ""
        print(f"  {'CSR ' + engine:14s} MAP {res.map_before:.4f} -> {res.map_after:.4f}{note}")
