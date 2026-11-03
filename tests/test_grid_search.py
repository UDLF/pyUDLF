"""
Smoke tests for pyUDLF.utils.gridSearch (legacy helpers).
"""

import pytest

from conftest import METHOD_CASES, make_input


@pytest.fixture
def cprr_input(udlf_template, data, tmp_path):
    return make_input(udlf_template, data, "CPRR", METHOD_CASES["CPRR"],
                      tmp_path / "out", tmp_path / "log.txt")


def test_sort_results_puts_failed_runs_last():
    from pyUDLF.utils.gridSearch import _sort_results

    results = [(0.5, "A"), ("NONE", "B"), (0.7, "C")]
    assert _sort_results(results) == [(0.7, "C"), (0.5, "A"), ("NONE", "B")]


def test_find_best_param(old_api, cprr_input):
    from pyUDLF.utils.gridSearch import find_best_param

    best = find_best_param(cprr_input, "CPRR", "PARAM_CPRR_K", [5, 10, 15])

    maps = best["MAP"]
    assert sorted(value for _, value in maps) == [5, 10, 15]
    assert [m for m, _ in maps] == sorted((m for m, _ in maps), reverse=True)
    assert all(isinstance(m, float) for m, _ in maps)
    assert set(best) == {"MAP", "P@5", "P@10", "P@20", "Recall@5", "Recall@10", "Recall@20"}


def test_find_best_method_ranks_failures_last(old_api, cprr_input):
    """All methods of the template run with L = 100; RLSIM keeps CK = 700 > N
    and fails, so it must be ranked last."""
    from pyUDLF.utils.gridSearch import find_best_method

    best = find_best_method(cprr_input, ranked_list_size=100, verbose=False)

    maps = best["MAP"]
    assert len(maps) == 11  # every method except NONE
    assert maps[-1] == ("NONE", "RLSIM")
    values = [m for m, _ in maps[:-1]]
    assert all(isinstance(m, float) for m in values)
    assert values == sorted(values, reverse=True)
    assert cprr_input.get_method_name()[0].strip() == "CPRR"  # restored
