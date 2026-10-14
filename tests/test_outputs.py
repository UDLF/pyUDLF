"""
Outputs of the legacy API: output paths, parsed log, individual gain and
ranked list visualization.
"""

import filecmp
from pathlib import Path

import numpy as np
import pytest

from conftest import METHOD_CASES, N, base_config, make_input, parse_map


def _input(udlf_template, data, tmp_path, method="CPRR", **kwargs):
    return make_input(udlf_template, data, method, METHOD_CASES[method],
                      tmp_path / "out", tmp_path / "log.txt", **kwargs)


# --------------------------------------------------------------------------
# Output paths (parser.parse_config)
# --------------------------------------------------------------------------

def test_get_rks_with_output_rk_format_all(old_api, udlf_template, data, tmp_path):
    """With ALL, UDLF writes <path>_num.txt, <path>_str.txt and html files."""
    inp = _input(udlf_template, data, tmp_path)
    inp.set_output_rk_format("ALL")
    inp.set_output_html_rk_per_file(N)  # one html file instead of N
    output = old_api.run(inp, get_output=True)

    assert output.rk_path == f"{tmp_path / 'out'}_num.txt"
    expected = [[int(x) for x in l.split()]
                for l in Path(output.rk_path).read_text().splitlines()]
    assert output.get_rks(top_k=100) == expected


def test_get_rks_with_string_output(old_api, udlf_template, data, tmp_path):
    inp = _input(udlf_template, data, tmp_path)
    inp.set_output_rk_format("STR")
    output = old_api.run(inp, get_output=True)

    rks = output.get_rks(top_k=3)
    assert rks[0][0] == "img_000.jpg"


@pytest.mark.parametrize("lines, expected", [
    # the output path is found whatever the order of the variables
    (["OUTPUT_FILE_PATH = /x/out", "OUTPUT_FILE_FORMAT = RK", "OUTPUT_RK_FORMAT = NUM"],
     {"rk_path": "/x/out.txt", "matrix_path": ""}),
    (["OUTPUT_FILE_FORMAT=MATRIX", "OUTPUT_FILE_PATH=/x/out"],
     {"rk_path": "", "matrix_path": "/x/out.txt"}),
    # variables not declared take the UDLF defaults (RK, NUM, "output")
    ([], {"rk_path": "output.txt", "log_path": "log.txt"}),
    (["OUTPUT_FILE = FALSE", "OUTPUT_FILE_PATH = /x/out"],
     {"rk_path": "", "matrix_path": "", "after_path": ""}),
    (["OUTPUT_RK_FORMAT = HTML", "OUTPUT_FILE_PATH = /x/out"], {"rk_path": ""}),
])
def test_parse_config_output_paths(tmp_path, lines, expected):
    from pyUDLF.utils.parser import parse_config

    cfg = tmp_path / "cfg.ini"
    cfg.write_text("\n".join(lines) + "\n")
    params = parse_config(str(cfg))
    assert {key: params[key] for key in expected} == expected


# --------------------------------------------------------------------------
# Parsed log (readData.parse_log)
# --------------------------------------------------------------------------

def test_metrics_are_numbers(old_api, udlf_template, data, tmp_path):
    output = old_api.run(_input(udlf_template, data, tmp_path), get_output=True)
    log = output.log_dict

    assert isinstance(log["Time"], float)
    assert set(log) == {"Time", "MAP", "P@5", "P@10", "P@20",
                        "Recall@5", "Recall@10", "Recall@20"}
    before, after = parse_map(tmp_path / "log.txt")
    assert log["MAP"]["Before"] == before and log["MAP"]["After"] == after
    assert log["MAP"]["Gain"] == pytest.approx((after - before) / before * 100, abs=0.01)


def test_get_log_reads_the_log_file(old_api, udlf_template, data, tmp_path):
    from pyUDLF.utils.outputType import OutputType

    output = old_api.run(_input(udlf_template, data, tmp_path), get_output=True)
    from_file = OutputType()
    from_file.log_path = output.log_path

    log = from_file.get_log()
    assert {k: v for k, v in log.items() if k != "Time"} == \
        {k: v for k, v in output.log_dict.items() if k != "Time"}


def test_fusion_log_has_results_after_fusion(old_api, data, tmp_path):
    sim = np.loadtxt(data["matrix_sim"])
    rk_sim = tmp_path / "rk_sim.txt"
    np.savetxt(rk_sim, np.argsort(-sim, axis=1, kind="stable"), fmt="%d")
    params = dict(METHOD_CASES["CPRR"], UDL_TASK="FUSION", NUM_INPUT_FUSION_FILES="2",
                  INPUT_FILES_FUSION_1=data["rk_num"], INPUT_FILES_FUSION_2=str(rk_sim))
    cfg = tmp_path / "cfg.ini"
    cfg.write_text(base_config(data, "CPRR", params, tmp_path / "out", tmp_path / "log"))

    output = old_api.runWithConfig(str(cfg), get_output=True)

    assert isinstance(output.log_dict["MAP"], float)
    assert 0 < output.log_dict["MAP"] <= 1


# --------------------------------------------------------------------------
# Individual gain
# --------------------------------------------------------------------------

@pytest.mark.parametrize("method", ["CPRR", "RDPAC"])
def test_individual_gain_matches_udlf_map(old_api, udlf_template, data, tmp_path, method):
    """Output lists have size L < N. Averaging the per-query values gives the
    MAP values written by UDLF in the log, before and after."""
    from pyUDLF.utils import evaluation, readData

    output = old_api.run(_input(udlf_template, data, tmp_path, method), get_output=True,
                         compute_individual_gain=True)

    gains = output.individual_gain_list
    assert len(gains) == N
    classes = readData.read_classes(data["lists"], data["classes"])
    after = readData.read_ranked_lists_file_numeric(output.rk_path)
    depth = len(after[0])
    before = readData.read_ranked_lists_file_numeric(data["rk_num"], top_k=depth)
    map_before, ap_before = evaluation.compute_map(before, classes, depth)
    map_after, ap_after = evaluation.compute_map(after, classes, depth)

    udlf_before, udlf_after = parse_map(tmp_path / "log.txt")
    assert map_before == pytest.approx(udlf_before, abs=1.5e-4)
    assert map_after == pytest.approx(udlf_after, abs=1.5e-4)
    assert [g for g, _ in gains] == [round(a - b, 4) for b, a in zip(ap_before, ap_after)]


def test_individual_gain_with_string_class_labels(old_api, udlf_template, data, tmp_path):
    numeric = old_api.run(_input(udlf_template, data, tmp_path), get_output=True,
                          compute_individual_gain=True)
    inp = _input(udlf_template, data, tmp_path)
    inp.set_classes_file(data["classes_str"])
    textual = old_api.run(inp, get_output=True, compute_individual_gain=True)

    assert len(textual.individual_gain_list) == N
    assert textual.individual_gain_list == numeric.individual_gain_list


def test_get_individual_gain_list_returns_gain_index_pairs(old_api, udlf_template, data,
                                                           tmp_path):
    output = old_api.run(_input(udlf_template, data, tmp_path), get_output=True,
                         compute_individual_gain=True)

    pairs = output.get_individual_gain_list()
    assert pairs[:3] == [(output.individual_gain_list[i][0], i) for i in range(3)]
    ranked = output.get_individual_gain_list(sort=True)
    assert all(isinstance(g, float) and isinstance(i, int) for g, i in ranked)
    assert [g for g, _ in ranked] == sorted((g for g, _ in pairs), reverse=True)


# --------------------------------------------------------------------------
# Visualization
# --------------------------------------------------------------------------

def test_visualization_paths_are_prepared(old_api, data, tmp_path):
    from pyUDLF.utils.outputType import OutputType

    params = {"out_file_format": "RK", "out_rk_format": "NUM",
              "images_path": str(tmp_path), "list_path": data["lists"],
              "classes_path": data["classes"]}

    assert old_api.prepare_visualization(params, OutputType()) is True


def test_save_ranked_list_image(old_api, udlf_template, data, tmp_path):
    Image = pytest.importorskip("PIL.Image")
    images = tmp_path / "images"
    images.mkdir()
    for name in Path(data["lists"]).read_text().split():
        Image.new("RGB", (16, 16), (128, 128, 128)).save(images / name)

    inp = _input(udlf_template, data, tmp_path)
    inp.set_input_images_path(str(images))
    output = old_api.run(inp, get_output=True, visualization=True)

    saved = output.save_rk_img(line=0, rk_size=5, img_path=str(tmp_path / "rk0.png"))
    with Image.open(saved) as img:
        assert img.size == (5 * 16, 16)
