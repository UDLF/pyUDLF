"""
Effectiveness measures for ranked lists, computed as UDLF does
(src/Evaluation/Effectiveness.cpp), so the values match the UDLF log.

In every function:
    rks          -> ranked lists, one per query (rks[i] is the list of query i);
                    a list of lists or a 2D numpy array of indices
    classes_list -> class label of each element, in the dataset order
                    (any hashable labels: ints, strings, ...)
    depth        -> number of positions considered; -1 means the whole lists.
                    A depth larger than the lists is reduced to their size.
"""

import numpy as np

from pyUDLF.utils.logger import get_logger

logger = get_logger(__name__)


def _resolve_depth(rks, depth, name="depth"):
    size = min(len(rk) for rk in rks)
    if depth == -1:
        return size
    if depth > size:
        logger.warning("%s=%d is larger than the ranked lists (%d); using %d.",
                       name, depth, size, size)
        return size
    return depth


def _hits(rks, classes_list, depth):
    """Boolean matrix (queries x depth): is position j of query i relevant?
    Also returns the class id of each element and the size of each class."""
    mapping = {}
    ids = np.array([mapping.setdefault(label, len(mapping)) for label in classes_list])
    sizes = np.bincount(ids)
    top = np.array([rk[:depth] for rk in rks], dtype=np.int64)
    return ids[top] == ids[:len(top), None], ids[:len(top)], sizes


def get_class_size_dict(class_list):
    class_size_dict = dict()
    for label in class_list:
        class_size_dict[label] = class_size_dict.get(label, 0) + 1
    return class_size_dict


def compute_map(rks, classes_list, map_depth=-1):
    """
    Mean Average Precision at map_depth.

    The average precision of a query is divided by min(depth, size of its
    class), as in UDLF.

    Returns:
        (MAP rounded to 4 decimals, list with the average precision of each query)
    """
    depth = _resolve_depth(rks, map_depth, "map_depth")
    hits, ids, sizes = _hits(rks, classes_list, depth)

    precision_at = np.cumsum(hits, axis=1) / np.arange(1, depth + 1)
    ap = (precision_at * hits).sum(axis=1) / np.minimum(depth, sizes[ids])

    return round(float(ap.mean()), 4), ap.tolist()


def compute_recall(rks, classes_list, r_depth=-1):
    """
    Recall at r_depth.

    As in UDLF, the recall is averaged over the queries of each class and then
    over the classes (classes have the same weight, whatever their size).

    Returns:
        (recall rounded to 4 decimals, list with the recall of each query)
    """
    depth = _resolve_depth(rks, r_depth, "r_depth")
    hits, ids, sizes = _hits(rks, classes_list, depth)

    recall = hits.sum(axis=1) / sizes[ids]
    queries_per_class = np.bincount(ids, minlength=len(sizes))
    present = queries_per_class > 0
    by_class = np.bincount(ids, weights=recall, minlength=len(sizes))[present] \
        / queries_per_class[present]

    return round(float(by_class.mean()), 4), recall.tolist()


def compute_precision(rks, classes_list, p_depth=-1):
    """
    Precision at p_depth.

    Returns:
        (precision rounded to 4 decimals, list with the precision of each query)
    """
    depth = _resolve_depth(rks, p_depth, "p_depth")
    hits, _, _ = _hits(rks, classes_list, depth)

    precision = hits.sum(axis=1) / depth

    return round(float(precision.mean()), 4), precision.tolist()


def compute_gain(before_rks, after_rks, classes_list, depth=-1, measure="MAP", verbose=True):
    """
    Gain of each query: measure after minus measure before.

    Returns:
        list of (gain rounded to 4 decimals, query index)
    """
    measure = measure.upper()
    functions = {"MAP": compute_map, "PRECISION": compute_precision,
                 "RECALL": compute_recall}
    if measure not in functions:
        raise ValueError(f"Unknown measure {measure!r}. Use one of {sorted(functions)}.")

    depth = _resolve_depth(after_rks, _resolve_depth(before_rks, depth))
    if verbose:
        logger.info("Calculating the gain for %s with depth %d", measure, depth)

    _, before_list = functions[measure](before_rks, classes_list, depth)
    _, after_list = functions[measure](after_rks, classes_list, depth)

    return [(round(after - before, 4), i)
            for i, (before, after) in enumerate(zip(before_list, after_list))]
