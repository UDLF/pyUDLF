"""
Generate the small synthetic dataset used by the test suite.

The dataset has N = 200 "images" split into 10 classes of 20 elements each.
Features are noisy samples around random class centers, so the original
ranked lists are imperfect and re-ranking methods have room to improve them.

Files written to ``tests/data/synthetic/`` (all in the formats UDLF expects):

- ``lists.txt``      one image name per line (``img_000.jpg`` ...)
- ``classes.txt``    ``name:class`` per line, numeric class labels
- ``classes_str.txt``  same, but with string class labels (``class_a`` ...)
- ``rk_num.txt``     numeric ranked lists, N x N, space separated, query first
- ``rk_str.txt``     the same ranked lists using image names
- ``matrix_dist.txt``  N x N euclidean distance matrix
- ``matrix_sim.txt``   N x N cosine similarity matrix

The generated files are committed, so the tests do not depend on the numpy
version. Run this script only to regenerate them:

    python tests/data/make_synthetic.py
"""

from pathlib import Path

import numpy as np

N_CLASSES = 10
PER_CLASS = 20
DIM = 32
NOISE = 1.4  # per-dimension std; gives MAP@100 ~0.55 on the original lists
SEED = 7

OUT_DIR = Path(__file__).resolve().parent / "synthetic"


def main() -> None:
    rng = np.random.default_rng(SEED)
    n = N_CLASSES * PER_CLASS

    centers = rng.normal(0.0, 1.0, size=(N_CLASSES, DIM))
    labels = np.repeat(np.arange(N_CLASSES), PER_CLASS)
    feats = centers[labels] + rng.normal(0.0, NOISE, size=(n, DIM))

    names = [f"img_{i:03d}.jpg" for i in range(n)]

    sq = (feats ** 2).sum(axis=1)
    dist = np.sqrt(np.maximum(sq[:, None] + sq[None, :] - 2 * feats @ feats.T, 0.0))
    np.fill_diagonal(dist, 0.0)
    unit = feats / np.linalg.norm(feats, axis=1, keepdims=True)
    sim = unit @ unit.T

    # stable sort keeps the query in the first position (distance 0)
    rk = np.argsort(dist, axis=1, kind="stable")
    assert (rk[:, 0] == np.arange(n)).all()

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    (OUT_DIR / "lists.txt").write_text("".join(f"{x}\n" for x in names))
    (OUT_DIR / "classes.txt").write_text(
        "".join(f"{x}:{c}\n" for x, c in zip(names, labels)))
    (OUT_DIR / "classes_str.txt").write_text(
        "".join(f"{x}:class_{chr(ord('a') + c)}\n" for x, c in zip(names, labels)))
    np.savetxt(OUT_DIR / "rk_num.txt", rk, fmt="%d")
    (OUT_DIR / "rk_str.txt").write_text(
        "".join(" ".join(names[j] for j in row) + "\n" for row in rk))
    np.savetxt(OUT_DIR / "matrix_dist.txt", dist, fmt="%.6f")
    np.savetxt(OUT_DIR / "matrix_sim.txt", sim, fmt="%.6f")

    print(f"Synthetic dataset written to {OUT_DIR} (N={n}, classes={N_CLASSES})")


if __name__ == "__main__":
    main()
