"""
Run every UDLF method on the same ranked lists and compare their MAP.

    python examples/compare_methods.py

Uses the synthetic dataset of the repository (200 elements, 10 classes).
UDLF computes the MAP up to the size of each method's output lists (MAP@L),
so the "before" value changes with L.
"""

from pathlib import Path

import numpy as np

from pyUDLF import UDLF

DATA = Path(__file__).resolve().parent.parent / "tests" / "data" / "synthetic"
rks = np.loadtxt(DATA / "rk_num.txt", dtype=int)
labels = [token.split(":")[1] for token in (DATA / "classes.txt").read_text().split()]

# Parameters for a dataset of 200 elements (the defaults assume larger datasets)
PARAMS = {
    "NONE": {"l": 100},
    "CPRR": {"l": 100, "k": 10},
    "LHRR": {"l": 100, "k": 10},
    "RDPAC": {"l": 50, "k_end": 10},
    "RFE": {"l": 100, "k": 10, "perform_ccs": False},
    "BFSTREE": {"l": 100, "k": 10},
    "CONTEXTRR": {"l": 25, "k": 7},
    "CORGRAPH": {"l": 100, "k": 10},
    "RKGRAPH": {"l": 100, "k": 10},
    "RECKNNGRAPH": {"l": 100, "k": 10},
    "RLRECOM": {"l": 100, "k": 8},
    "RLSIM": {"topk": 10, "ck": 100},
}

udlf = UDLF()
results = []
for method in UDLF.methods():
    res = udlf.run(method, ranked_lists=rks, params=PARAMS[method], classes=labels)
    results.append((res.map_after, method, res))

print(f"{'Method':12s} {'MAP before':>10s} {'MAP after':>10s} {'Gain':>8s} {'P@10':>7s} {'Time':>8s}")
for map_after, method, res in sorted(results, key=lambda r: r[0], reverse=True):
    print(f"{method:12s} {res.map_before:10.4f} {map_after:10.4f} "
          f"{res.metrics['gain']['MAP']:7.1f}% {res.metrics['after']['P@10']:7.4f} {res.time:7.3f}s")
