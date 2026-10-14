"""
Effectiveness measures in Python (pyUDLF.utils.evaluation) must give the same
values UDLF writes in its log.
"""

import re
from pathlib import Path

import pytest

from conftest import METHOD_CASES, PRECISIONS, RECALLS, make_input
from pyUDLF.utils import evaluation


def _log_value(log_path, name, section):
    """Value of a measure in the Before or After section of a UDLF log."""
    text = Path(log_path).read_text()
    block = text.split(" Before:")[1] if section == "Before" else text.split(" After:")[1]
    return float(re.search(rf"^\s*{re.escape(name)}\s+([0-9.]+)", block, re.M).group(1))


@pytest.fixture
def udlf_run(old_api, udlf_template, data, tmp_path):
    """A CPRR run: (ranked lists after, classes, log path)."""
    from pyUDLF.utils import readData

    inp = make_input(udlf_template, data, "CPRR", METHOD_CASES["CPRR"],
                     tmp_path / "out", tmp_path / "log.txt")
    output = old_api.run(inp, get_output=True)
    rks = readData.read_ranked_lists_file_numeric(output.rk_path)
    classes = readData.read_classes(data["lists"], data["classes"])
    return rks, classes, tmp_path / "log.txt"


def test_measures_match_udlf_log(udlf_run):
    rks, classes, log = udlf_run
    tolerance = 1.5e-4  # UDLF computes in float32 and prints 4 decimals

    for k in map(int, PRECISIONS.split(",")):
        value, _ = evaluation.compute_precision(rks, classes, k)
        assert value == pytest.approx(_log_value(log, f"P@{k}", "After"), abs=tolerance)
    for k in map(int, RECALLS.split(",")):
        value, _ = evaluation.compute_recall(rks, classes, k)
        assert value == pytest.approx(_log_value(log, f"Recall@{k}", "After"), abs=tolerance)
    value, _ = evaluation.compute_map(rks, classes)  # default depth: whole lists (L)
    assert value == pytest.approx(_log_value(log, "MAP", "After"), abs=tolerance)


def test_map_divides_by_min_of_depth_and_class_size():
    # query 0 has 3 relevant items (class 0); with depth 2 both positions hit
    classes = [0, 0, 0, 1]
    rks = [[0, 1], [1, 0], [2, 0], [3, 0]]
    _, per_query = evaluation.compute_map(rks, classes, map_depth=2)

    assert per_query[0] == pytest.approx(1.0)        # 2 hits / min(2, 3)
    assert per_query[3] == pytest.approx(1.0)        # 1 hit / min(2, 1)


def test_recall_averages_classes_with_equal_weight():
    # class 0: 3 queries, each finds 1 of 3 relevant items in the top 1 -> 1/3
    # class 1: 1 query, finds its only relevant item -> 1
    classes = [0, 0, 0, 1]
    rks = [[0], [1], [2], [3]]
    value, per_query = evaluation.compute_recall(rks, classes, 1)

    assert per_query == pytest.approx([1 / 3, 1 / 3, 1 / 3, 1.0])
    assert value == pytest.approx(round((1 / 3 + 1) / 2, 4))  # not the mean of queries


def test_compute_recall_with_default_depth():
    value, _ = evaluation.compute_recall([[0, 1], [1, 0]], [0, 0])
    assert value == 1.0


def test_default_depth_is_the_ranked_list_size():
    """The default used to be the number of queries, which crashed when the
    lists are shorter than the dataset."""
    classes = [0, 0, 1, 1]
    rks = [[0, 1], [1, 0], [2, 3], [3, 2]]
    assert evaluation.compute_map(rks, classes)[0] == 1.0
    assert evaluation.compute_precision(rks, classes)[0] == 1.0


def test_depth_larger_than_lists_is_reduced(caplog):
    classes = [0, 0, 1, 1]
    rks = [[0, 1], [1, 0], [2, 3], [3, 2]]
    assert evaluation.compute_precision(rks, classes, p_depth=10)[0] == 1.0
    assert "larger than the ranked lists" in caplog.text


def test_compute_gain_rejects_unknown_measure():
    with pytest.raises(ValueError, match="measure"):
        evaluation.compute_gain([[0]], [[0]], [0], measure="NDCG")
