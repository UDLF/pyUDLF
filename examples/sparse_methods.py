"""
Compare UDLF 1.70 with Sparse UDLF on the same input.

    python examples/sparse_methods.py --sparse-bin path/to/Sparse_UDLF/bin

(or set the UDLF_SPARSE_BIN environment variable; scripts/build_sparse.sh
builds Sparse UDLF into .udlf/Sparse_UDLF, which is used when present).

Uses the synthetic dataset of the repository (200 elements, 10 classes).
Sparse UDLF implements CPRR, LHRR, RDPAC, RFE and BFSTREE with sparse matrices,
for datasets where the dense N x N matrices of UDLF do not fit in memory; on
the same input it returns the same ranked lists as UDLF.
"""

import argparse
import os
from pathlib import Path

import numpy as np

from pyUDLF import UDLF, UDLFRunError

REPO = Path(__file__).resolve().parent.parent
DATA = REPO / "tests" / "data" / "synthetic"
BUILT = REPO / ".udlf" / "Sparse_UDLF" / "bin"

parser = argparse.ArgumentParser(description="Compare UDLF 1.70 with Sparse UDLF.")
parser.add_argument("--sparse-bin", default=os.environ.get("UDLF_SPARSE_BIN")
                    or (BUILT if BUILT.is_dir() else None))
args = parser.parse_args()
if not args.sparse_bin:
    raise SystemExit("Sparse UDLF not found: build it with scripts/build_sparse.sh, "
                     "or pass --sparse-bin / set UDLF_SPARSE_BIN.")

rks = np.loadtxt(DATA / "rk_num.txt", dtype=int)
labels = [token.split(":")[1] for token in (DATA / "classes.txt").read_text().split()]
params = {
    "CPRR": {"l": 100, "k": 10},
    "LHRR": {"l": 100, "k": 10},
    "RDPAC": {"l": 50, "k_end": 10},
    "BFSTREE": {"l": 100, "k": 10},
    "RFE": {"l": 100, "k": 10, "perform_ccs": False},
}

udlf = UDLF()
sparse = UDLF(bin_path=args.sparse_bin, backend="sparse")

print(f"{'Method':9s} {'UDLF 1.70':>18s} {'Sparse UDLF':>18s}   same lists")
for method, p in params.items():
    reference = udlf.run(method, ranked_lists=rks, params=p, classes=labels)
    try:
        res = sparse.run(method, ranked_lists=rks, params=p, classes=labels)
    except UDLFRunError as e:
        print(f"{method:9s} {reference.map_before:.4f} -> {reference.map_after:.4f}   "
              f"not run: {e.problems[-1]}")
        continue
    same = "yes" if np.array_equal(res.ranked_lists, reference.ranked_lists) else "no"
    print(f"{method:9s} {reference.map_before:.4f} -> {reference.map_after:.4f}   "
          f"{res.map_before:.4f} -> {res.map_after:.4f}   {same}")
