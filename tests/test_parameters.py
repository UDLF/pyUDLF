"""
Parameter handling of the legacy API (InputType).
"""

import pytest

from conftest import METHOD_CASES, make_input


@pytest.fixture
def inp(udlf_template):
    from pyUDLF.utils.inputType import InputType
    return InputType(config_path=str(udlf_template))


def _value(inp, name):
    return inp.get_param(name)[0].strip()


# --------------------------------------------------------------------------
# set_method_parameters
# --------------------------------------------------------------------------

def test_set_method_parameters_keeps_values_not_passed(inp):
    inp.set_ranked_lists_size(150)
    inp.set_param("PARAM_CPRR_T", 5)
    inp.set_method_parameters("CPRR", k=10)

    assert (_value(inp, "PARAM_CPRR_L"), _value(inp, "PARAM_CPRR_K"),
            _value(inp, "PARAM_CPRR_T")) == ("150", "10", "5")


def test_set_method_parameters_can_reset_defaults(inp):
    inp.set_ranked_lists_size(150)
    inp.set_method_parameters("CPRR", reset_defaults=True, k=10)

    assert (_value(inp, "PARAM_CPRR_L"), _value(inp, "PARAM_CPRR_K"),
            _value(inp, "PARAM_CPRR_T")) == ("400", "10", "2")


def test_set_method_parameters_names_are_case_insensitive(inp):
    inp.set_method_parameters("cprr", L=120, K=12)
    assert (_value(inp, "PARAM_CPRR_L"), _value(inp, "PARAM_CPRR_K")) == ("120", "12")


def test_set_method_parameters_rejects_unknown_names(inp):
    with pytest.raises(ValueError, match="alpha"):
        inp.set_method_parameters("CPRR", k=10, alpha=0.5)
    assert _value(inp, "PARAM_CPRR_K") != "10"  # nothing was changed


def test_set_method_parameters_accepts_int_for_float(inp):
    inp.set_method_parameters("RDPAC", p=1)
    assert float(_value(inp, "PARAM_RDPAC_P")) == 1.0


@pytest.mark.parametrize("method, kwargs", [
    ("CPRR", {"k": True}),          # bool is not an int
    ("CPRR", {"k": 2.5}),
    ("RDPAC", {"p": "0.5"}),
    ("CONTEXTRR", {"optimizations": 1}),
])
def test_set_method_parameters_rejects_wrong_types(inp, method, kwargs):
    with pytest.raises(ValueError, match="Invalid type"):
        inp.set_method_parameters(method, **kwargs)


# --------------------------------------------------------------------------
# set_param
# --------------------------------------------------------------------------

@pytest.mark.parametrize("name, value, stored", [
    ("PARAM_CPRR_L", 100, "100"),
    ("PARAM_CPRR_L", "100", "100"),         # numeric strings are accepted
    ("PARAM_RLSIM_METRIC", " rbo ", "RBO"),  # enums are normalized
    ("OUTPUT_FILE", True, "TRUE"),
    ("PARAM_RDPAC_P", 1, "1.0"),
    ("param_cprr_k", 7, "7"),                # name is case-insensitive
])
def test_set_param_normalizes_values(inp, name, value, stored):
    inp.set_param(name, value)
    assert _value(inp, name.upper()) == stored


@pytest.mark.parametrize("name, value", [
    ("PARAM_RLSIM_METRIC", "NOT_A_METRIC"),
    ("PARAM_CPRR_K", "abc"),
    ("PARAM_CPRR_K", -1),
    ("PARAM_CPRR_K", True),
    ("OUTPUT_FILE", "yes"),
    ("PARAM_RKGRAPH_P", 2.0),  # must be in [0, 1]
])
def test_set_param_rejects_invalid_values(inp, name, value):
    with pytest.raises(ValueError):
        inp.set_param(name, value)


def test_set_param_on_missing_parameter_raises(inp):
    with pytest.raises(KeyError, match="add_new_parameter"):
        inp.set_param("PARAM_DOES_NOT_EXIST", 1)


def test_set_param_keeps_free_values_for_unknown_rules(inp):
    """Parameters without validation rules (e.g. paths) are stored as given."""
    inp.set_param("PARAM_RFE_CCS_PATH", "some/dir/ccs.txt")
    assert _value(inp, "PARAM_RFE_CCS_PATH") == "some/dir/ccs.txt"


# --------------------------------------------------------------------------
# add_new_parameter
# --------------------------------------------------------------------------

def test_add_new_parameter_with_int_value_runs(old_api, udlf_template, data, tmp_path):
    """New parameters are stored as text, so write_config works for any value."""
    inp = make_input(udlf_template, data, "CPRR", METHOD_CASES["CPRR"],
                     tmp_path / "out", tmp_path / "log.txt")
    inp.add_new_parameter("PARAM_CPRR_EXTRA", 1)

    inp.write_config(str(tmp_path / "cfg.ini"))
    assert "PARAM_CPRR_EXTRA" in (tmp_path / "cfg.ini").read_text()
    assert old_api.run(inp, get_output=True)


def test_add_new_parameter_rejects_existing_name(inp):
    with pytest.raises(ValueError, match="set_param"):
        inp.add_new_parameter("PARAM_CPRR_L", 100)
