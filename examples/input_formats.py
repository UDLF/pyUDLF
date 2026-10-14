"""
The input formats UDLF accepts: ranked lists (numpy array, numeric file,
file with element names) and distance / similarity matrices. Here they all
describe the same neighbourhoods, so CPRR gives the same re-ranked lists.

    python examples/input_formats.py

Uses the synthetic dataset of the repository (200 elements, 10 classes).
"""

from pathlib import Path

import numpy as np

from pyUDLF import UDLF

DATA = Path(__file__).resolve().parent.parent / "tests" / "data" / "synthetic"
labels = [token.split(":")[1] for token in (DATA / "classes.txt").read_text().split()]
distances = np.loadtxt(DATA / "matrix_dist.txt")
params = {"l": 100, "k": 10}
udlf = UDLF()

runs = {
    # ranked lists: one row per query, element indices
    "ranked lists (numpy)": udlf.run("CPRR", ranked_lists=np.loadtxt(DATA / "rk_num.txt", dtype=int),
                                     params=params, classes=labels),
    "ranked lists (file)": udlf.run("CPRR", ranked_lists=DATA / "rk_num.txt",
                                    params=params, classes=labels),
    # ranked lists with element names, plus the UDLF lists and classes files
    "ranked lists (names)": udlf.run("CPRR", ranked_lists=DATA / "rk_str.txt", names=DATA / "lists.txt",
                                     classes=DATA / "classes.txt", params=params),
    # N x N matrices: distances (file or numpy), or similarities (larger = closer)
    "distance matrix (file)": udlf.run("CPRR", matrix=DATA / "matrix_dist.txt", matrix_type="dist",
                                       params=params, classes=labels),
    "similarity matrix": udlf.run("CPRR", matrix=1 / (1 + distances), matrix_type="sim",
                                  params=params, classes=labels),
}

reference = runs["ranked lists (numpy)"].ranked_lists
for name, res in runs.items():
    same = "same lists" if np.array_equal(res.ranked_lists, reference) else "different lists"
    print(f"{name:22s} MAP {res.map_before:.4f} -> {res.map_after:.4f}   ({same})")

# The output can also be a distance (or similarity) matrix
res = udlf.run("CPRR", ranked_lists=reference, params=params, classes=labels, output="matrix")
print(f"\nOutput as a matrix: {res.matrix.shape}")
