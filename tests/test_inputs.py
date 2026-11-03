"""
Input handling of the legacy API: in-memory ranked lists and FUSION tasks.
"""

import filecmp
from pathlib import Path

import numpy as np
import pytest

from conftest import METHOD_CASES, N, base_config, make_input, run_direct


def _load_rk(path):
    return np.loadtxt(path, dtype=np.int64)


def _cprr_input(udlf_template, data, tmp_path, tag="out"):
    return make_input(udlf_template, data, "CPRR", METHOD_CASES["CPRR"],
                      tmp_path / tag, tmp_path / f"{tag}_log.txt")


# --------------------------------------------------------------------------
# In-memory ranked lists
# --------------------------------------------------------------------------

@pytest.mark.parametrize("kind", ["list_of_rows", "numpy_2d", "wrapped_in_list"])
def test_in_memory_ranked_lists_match_file_input(old_api, udlf_template, data,
                                                 tmp_path, kind):
    rks = _load_rk(data["rk_num"])
    value = {"list_of_rows": rks.tolist(),
             "numpy_2d": rks,
             "wrapped_in_list": [rks.tolist()]}[kind]

    from_file = _cprr_input(udlf_template, data, tmp_path, "file")
    assert old_api.run(from_file, get_output=True)

    in_memory = _cprr_input(udlf_template, data, tmp_path, "memory")
    in_memory.set_input_files(value)
    assert in_memory.get_task()[0].strip() == "UDL"
    written = in_memory.get_input_files()
    assert Path(written).is_file() and written.startswith(str(tmp_path))
    assert old_api.run(in_memory, get_output=True)

    assert filecmp.cmp(tmp_path / "file.txt", tmp_path / "memory.txt", shallow=False)


def test_in_memory_input_sets_numeric_ranked_list_format(udlf_template, data):
    from pyUDLF.utils.inputType import InputType

    inp = InputType(config_path=str(udlf_template))
    inp.set_input_files(_load_rk(data["rk_num"]))

    assert inp.get_param("INPUT_FILE_FORMAT")[0].strip() == "RK"
    assert inp.get_param("INPUT_RK_FORMAT")[0].strip() == "NUM"


def test_in_memory_input_rejects_non_integer_values(udlf_template):
    from pyUDLF.utils.inputType import InputType

    inp = InputType(config_path=str(udlf_template))
    with pytest.raises(ValueError, match="integer"):
        inp.set_input_files(np.random.default_rng(0).random((10, 10)))


@pytest.mark.parametrize("kind", ["list_of_arrays", "array_3d"])
def test_in_memory_matrices_become_fusion_files(udlf_template, data, kind):
    from pyUDLF.utils.inputType import InputType

    rks = _load_rk(data["rk_num"])
    second = rks[:, :150] if kind == "list_of_arrays" else rks[::-1]
    value = [rks, second] if kind == "list_of_arrays" else np.stack([rks, second])
    inp = InputType(config_path=str(udlf_template))
    inp.set_input_files(value)

    files = inp.get_input_files()
    assert inp.get_task()[0].strip() == "FUSION"
    assert len(files) == 2
    assert np.array_equal(_load_rk(files[1]), second)


# --------------------------------------------------------------------------
# FUSION
# --------------------------------------------------------------------------

@pytest.fixture
def fusion_files(data, tmp_path):
    """Three different numeric ranked lists of the synthetic dataset."""
    dist = np.loadtxt(data["matrix_dist"])
    sim = np.loadtxt(data["matrix_sim"])
    noisy = dist + np.random.default_rng(1).normal(0, 0.3, dist.shape)
    np.fill_diagonal(noisy, 0)
    paths = []
    for name, rk in [("rk_dist", np.argsort(dist, axis=1, kind="stable")),
                     ("rk_sim", np.argsort(-sim, axis=1, kind="stable")),
                     ("rk_noisy", np.argsort(noisy, axis=1, kind="stable"))]:
        path = tmp_path / f"{name}.txt"
        np.savetxt(path, rk, fmt="%d")
        paths.append(str(path))
    return paths


def _fusion_config(data, files, out, log):
    params = dict(METHOD_CASES["CPRR"], UDL_TASK="FUSION",
                  NUM_INPUT_FUSION_FILES=str(len(files)))
    params.update({f"INPUT_FILES_FUSION_{i}": f for i, f in enumerate(files, 1)})
    return base_config(data, "CPRR", params, out, log)


def test_fusion_sets_number_of_input_files(udlf_template, data, fusion_files):
    from pyUDLF.utils.inputType import InputType

    inp = InputType(config_path=str(udlf_template))
    inp.set_input_files(fusion_files)

    assert inp.get_task()[0].strip() == "FUSION"
    assert int(inp.get_param("NUM_INPUT_FUSION_FILES")[0]) == 3
    assert inp.get_input_files() == fusion_files


def test_fusion_of_three_files_matches_direct_run(old_api, udlf_bin, udlf_template, data,
                                                  tmp_path, fusion_files):
    inp = _cprr_input(udlf_template, data, tmp_path, "wrapper")
    inp.set_input_files(fusion_files)
    assert old_api.run(inp, get_output=True)

    proc = run_direct(udlf_bin, _fusion_config(data, fusion_files, tmp_path / "direct",
                                               tmp_path / "direct_log.txt"), tmp_path)
    assert proc.returncode == 0, proc.stdout
    assert filecmp.cmp(tmp_path / "wrapper.txt", tmp_path / "direct.txt", shallow=False)

    # the third file is really used: fusing only the first two gives other results
    proc = run_direct(udlf_bin, _fusion_config(data, fusion_files[:2], tmp_path / "two",
                                               tmp_path / "two_log.txt"), tmp_path)
    assert proc.returncode == 0, proc.stdout
    assert not filecmp.cmp(tmp_path / "wrapper.txt", tmp_path / "two.txt", shallow=False)


def test_add_input_files_appends_to_fusion(udlf_template, data, fusion_files):
    from pyUDLF.utils.inputType import InputType

    inp = InputType(config_path=str(udlf_template))
    inp.set_input_files(fusion_files[:2])
    inp.add_input_files(fusion_files[2])

    assert int(inp.get_param("NUM_INPUT_FUSION_FILES")[0]) == 3
    assert inp.get_input_files() == fusion_files


def test_fewer_fusion_files_after_more(udlf_template, data, fusion_files):
    """Entries left over from a previous, longer list are ignored."""
    from pyUDLF.utils.inputType import InputType

    inp = InputType(config_path=str(udlf_template))
    inp.set_input_files(fusion_files)
    inp.set_input_files(fusion_files[1:])

    assert inp.get_input_files() == fusion_files[1:]


def test_add_input_files_requires_fusion_task(udlf_template, data):
    from pyUDLF.utils.inputType import InputType

    inp = InputType(config_path=str(udlf_template))
    inp.set_input_files(data["rk_num"])
    with pytest.raises(ValueError, match="FUSION"):
        inp.add_input_files(data["rk_num"])
