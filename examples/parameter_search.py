"""
Search the best k and l of a method (grid search).

    python examples/parameter_search.py

Uses the synthetic dataset of the repository (200 elements, 10 classes).
"""

from pathlib import Path

import numpy as np

from pyUDLF import UDLF

DATA = Path(__file__).resolve().parent.parent / "tests" / "data" / "synthetic"
rks = np.loadtxt(DATA / "rk_num.txt", dtype=int)
labels = [token.split(":")[1] for token in (DATA / "classes.txt").read_text().split()]

METHOD = "CPRR"
K_VALUES = [5, 10, 15, 20, 30]
L_VALUES = [50, 100, 150]

udlf = UDLF()
maps = np.zeros((len(L_VALUES), len(K_VALUES)))
for i, l in enumerate(L_VALUES):
    for j, k in enumerate(K_VALUES):
        res = udlf.run(METHOD, ranked_lists=rks, params={"l": l, "k": k}, classes=labels)
        maps[i, j] = res.map_after

print(f"{METHOD}: MAP after re-ranking (rows: l, columns: k)")
print("l \\ k " + "".join(f"{k:>8d}" for k in K_VALUES))
for l, row in zip(L_VALUES, maps):
    print(f"{l:5d} " + "".join(f"{value:8.4f}" for value in row))

i, j = np.unravel_index(np.argmax(maps), maps.shape)
print(f"\nBest: l = {L_VALUES[i]}, k = {K_VALUES[j]} (MAP {maps[i, j]:.4f})")
