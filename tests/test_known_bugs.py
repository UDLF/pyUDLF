"""
Known bugs of the legacy API, found during the 2026-10 review.

Each test asserts the *correct* behaviour and is marked as a strict xfail.
When a fix lands, the test starts passing, strict xfail turns that into a
failure, and the marker must be removed in the same change. This way every
bug fix comes with a regression test.
"""

from pathlib import Path

import pytest

from conftest import METHOD_CASES, N, make_input

known_bug = pytest.mark.xfail(strict=True, reason="known bug, see module docstring")


def _cprr_input(udlf_template, data, tmp_path, **kwargs):
    return make_input(udlf_template, data, "CPRR", METHOD_CASES["CPRR"],
                      tmp_path / "out", tmp_path / "log.txt", **kwargs)


# --------------------------------------------------------------------------
# Outputs
# --------------------------------------------------------------------------

@known_bug
def test_get_rks_with_output_rk_format_all(old_api, udlf_template, data, tmp_path):
    """With OUTPUT_RK_FORMAT=ALL (the template default) UDLF writes
    <path>_num.txt, but the wrapper looks for <path>.txt."""
    inp = _cprr_input(udlf_template, data, tmp_path)
    inp.set_output_rk_format("ALL")
    inp.set_output_html_rk_per_file(N)  # one html file instead of N
    output = old_api.run(inp, get_output=True)

    assert len(output.get_rks(top_k=10)) == N


@known_bug
def test_individual_gain_when_l_smaller_than_n(old_api, udlf_template, data, tmp_path):
    """The gain is computed with depth = N over output lists of size L < N,
    raising IndexError (caught and turned into an empty list)."""
    inp = _cprr_input(udlf_template, data, tmp_path)
    output = old_api.run(inp, get_output=True, compute_individual_gain=True)

    assert len(output.individual_gain_list) == N


@known_bug
def test_individual_gain_with_string_class_labels(old_api, udlf_template, data, tmp_path):
    """read_classes converts labels with int(), so 'name:class_a' fails."""
    inp = _cprr_input(udlf_template, data, tmp_path)
    inp.set_classes_file(data["classes_str"])
    output = old_api.run(inp, get_output=True, compute_individual_gain=True, depth=100)

    assert len(output.individual_gain_list) == N


@known_bug
def test_visualization_paths_are_prepared(old_api, udlf_template, data, tmp_path):
    """prepare_visualization checks the list and classes *files* with isdir,
    so it always fails (run() only logs the error and continues)."""
    from pyUDLF.utils.outputType import OutputType

    params = {"out_file_format": "RK", "out_rk_format": "NUM",
              "images_path": str(tmp_path), "list_path": data["lists"],
              "classes_path": data["classes"]}

    assert old_api.prepare_visualization(params, OutputType()) is True


@known_bug
def test_metrics_are_numbers(old_api, udlf_template, data, tmp_path):
    """log_dict values are strings such as '0.6382', '27.6%' and ' 0.03 s'."""
    output = old_api.run(_cprr_input(udlf_template, data, tmp_path), get_output=True)

    assert isinstance(output.log_dict["MAP"]["After"], float)


# --------------------------------------------------------------------------
# Evaluation helpers
# --------------------------------------------------------------------------

@known_bug
def test_compute_recall_with_default_depth():
    """compute_recall assigns the default depth to a typo variable (r instead
    of r_depth), so it always returns 0."""
    from pyUDLF.utils.evaluation import compute_recall

    value, _ = compute_recall([[0, 1], [1, 0]], [0, 0])

    assert value == 1.0


@known_bug
def test_compute_map_matches_udlf_definition():
    """UDLF divides the average precision by min(L, class size); the wrapper
    divides by the class size, so values differ when L < class size."""
    from pyUDLF.utils.evaluation import compute_map

    # 1 query of class 0 (3 relevant items), ranked list of size L = 2
    classes = [0, 0, 0, 1]
    rks = [[0, 1], [1, 0], [2, 0], [3, 0]]
    value, per_query = compute_map(rks, classes, map_depth=2)

    assert per_query[0] == pytest.approx(1.0)  # 2 hits in 2 positions / min(2, 3)
