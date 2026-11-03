"""
Fuse the ranked lists of two descriptors of the same dataset (FUSION task).

    python examples/fusion.py

Uses the synthetic dataset of the repository (200 elements, 10 classes): the
two "descriptors" are the Euclidean distance and the cosine similarity of the
same features.
"""

from pathlib import Path

import numpy as np

from pyUDLF import UDLF

DATA = Path(__file__).resolve().parent.parent / "tests" / "data" / "synthetic"
labels = [token.split(":")[1] for token in (DATA / "classes.txt").read_text().split()]
by_distance = np.argsort(np.loadtxt(DATA / "matrix_dist.txt"), axis=1, kind="stable")
by_cosine = np.argsort(-np.loadtxt(DATA / "matrix_sim.txt"), axis=1, kind="stable")
params = {"l": 100, "k": 10}

udlf = UDLF()
for name, rks in [("Euclidean", by_distance), ("cosine", by_cosine)]:
    res = udlf.run("CPRR", ranked_lists=rks, params=params, classes=labels)
    print(f"{name:10s} alone: MAP {res.map_before:.4f} -> {res.map_after:.4f}")

fused = udlf.fuse("CPRR", [by_distance, by_cosine], params=params, classes=labels)
print(f"Fused (CPRR): MAP {fused.map_after:.4f}")   # FUSION reports the result after fusion
