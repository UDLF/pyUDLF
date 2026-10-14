"""
Look at the effect of a method on each query: which queries improved, which
got worse, and how the top of their ranked lists changed. Also saves the
re-ranked lists.

    python examples/per_query_analysis.py

Uses the synthetic dataset of the repository (200 elements, 10 classes).
"""

import tempfile
from pathlib import Path

import numpy as np

from pyUDLF import UDLF

DATA = Path(__file__).resolve().parent.parent / "tests" / "data" / "synthetic"
rks = np.loadtxt(DATA / "rk_num.txt", dtype=int)
labels = np.array([int(token.split(":")[1]) for token in (DATA / "classes.txt").read_text().split()])

res = UDLF().run("LHRR", ranked_lists=rks, params={"l": 100, "k": 10}, classes=labels)
before, after = res.per_query("MAP")   # average precision of each query
gain = after - before

print(f"MAP {res.map_before:.4f} -> {res.map_after:.4f}")
print(f"{(gain > 0).sum()} queries improved, {(gain < 0).sum()} got worse, "
      f"{(gain == 0).sum()} unchanged\n")


def top(ranked_list, query, n=10):
    """'+' for an element of the query's class, '.' otherwise."""
    return "".join("+" if labels[e] == labels[query] else "." for e in ranked_list[:n])


for title, queries in [("Most improved", np.argsort(gain)[::-1][:3]),
                       ("Got worse", np.argsort(gain)[:3])]:
    print(title)
    for q in queries:
        print(f"  query {q:3d}: AP {before[q]:.3f} -> {after[q]:.3f}   "
              f"top 10 before {top(rks[q], q)}  after {top(res.ranked_lists[q], q)}")

out = Path(tempfile.gettempdir()) / "lhrr_ranked_lists.txt"
np.savetxt(out, res.ranked_lists, fmt="%d")   # same format UDLF reads
print(f"\nRe-ranked lists saved to {out}")
