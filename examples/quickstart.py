import numpy as np
from pyUDLF import UDLF

# A small dataset: 200 elements in 10 classes, with noisy 32-D features
rng = np.random.default_rng(7)
labels = np.repeat(np.arange(10), 20)
features = rng.normal(size=(10, 32))[labels] + rng.normal(scale=1.4, size=(200, 32))

# Ranked lists: each row is a query, with all elements sorted by distance
distances = np.linalg.norm(features[:, None] - features[None], axis=2)
ranked_lists = np.argsort(distances, axis=1, kind="stable")

# Re-rank them with CPRR (needs the UDLF binary: run `pyudlf download` once)
udlf = UDLF()
res = udlf.run("CPRR", ranked_lists=ranked_lists, params={"l": 100, "k": 10},
               classes=labels)

print(res)                       # Result(method='CPRR', ranked_lists=(200, 100), MAP 0.5471 -> 0.7602)
print(res.metrics["before"]["P@10"], "->", res.metrics["after"]["P@10"])   # 0.631 -> 0.8315
before, after = res.per_query()  # average precision of each query
print((after > before).sum(), "of 200 queries improved")                  # 186 of 200 queries improved
