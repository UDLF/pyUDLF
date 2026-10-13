"""
Effectiveness measures for ranked lists, computed as UDLF does
(src/Evaluation/Effectiveness.cpp), so the values match the UDLF log.

In every function:
    rks          -> ranked lists, one per query (rks[i] is the list of query i)
    classes_list -> class label of each element, in the dataset order
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
    class_size_dict = get_class_size_dict(classes_list)

    map_list = []
    for i, rk in enumerate(rks):
        cl_i = classes_list[i]
        hits = 0
        acum = 0.0
        for j in range(depth):
            if classes_list[rk[j]] == cl_i:
                hits += 1
                acum += hits / (j + 1)
        map_list.append(acum / min(depth, class_size_dict[cl_i]))

    return round(float(np.mean(map_list)), 4), map_list


def compute_recall(rks, classes_list, r_depth=-1):
    """
    Recall at r_depth.

    As in UDLF, the recall is averaged over the queries of each class and then
    over the classes (classes have the same weight, whatever their size).

    Returns:
        (recall rounded to 4 decimals, list with the recall of each query)
    """
    depth = _resolve_depth(rks, r_depth, "r_depth")
    class_size_dict = get_class_size_dict(classes_list)

    recall_list = []
    for i, rk in enumerate(rks):
        cl_i = classes_list[i]
        hits = sum(1 for j in range(depth) if classes_list[rk[j]] == cl_i)
        recall_list.append(hits / class_size_dict[cl_i])

    by_class = {}
    for i, value in enumerate(recall_list):
        by_class.setdefault(classes_list[i], []).append(value)
    r_value = np.mean([np.mean(values) for values in by_class.values()])

    return round(float(r_value), 4), recall_list


def compute_precision(rks, classes_list, p_depth=-1):
    """
    Precision at p_depth.

    Returns:
        (precision rounded to 4 decimals, list with the precision of each query)
    """
    depth = _resolve_depth(rks, p_depth, "p_depth")

    precision_list = []
    for i, rk in enumerate(rks):
        cl_i = classes_list[i]
        hits = sum(1 for j in range(depth) if classes_list[rk[j]] == cl_i)
        precision_list.append(hits / depth)

    return round(float(np.mean(precision_list)), 4), precision_list


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
