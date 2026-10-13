"""
The parameter schema of pyUDLF must match the UDLF version it targets.

UDLF declares its parameters (name, type, allowed values) in config/*.conf,
compiled into the binary, and their reference values in bin/config.ini.
These tests compare pyUDLF's schema with the sources of the UDLF build used
by the test suite (scripts/build_udlf.sh), so updating UDLF shows exactly
what changed.
"""

import re
from pathlib import Path

import pytest

from pyUDLF.utils.parser import read_config_values
from pyUDLF.utils.validations import METHOD_PARAMS, VALIDATIONS

# wrapper rule type -> UDLF type
RULE_TYPES = {"uint": "UINT", "float": "DBL", "bool": "BOL", "enum": "STR",
              "list_uint": "STR"}
PY_TYPES = {int: "UINT", float: "DBL", bool: "BOL", str: "STR"}

from pyUDLF.run_calls import bundled_config_path

BUNDLED_CONFIG = Path(bundled_config_path)


@pytest.fixture(scope="session")
def udlf_source(udlf_bin):
    root = udlf_bin.parent.parent
    if not (root / "config" / "general.conf").is_file():
        pytest.skip(f"UDLF sources not found at {root}")
    return root


@pytest.fixture(scope="session")
def udlf_conf(udlf_source):
    """{variable: (type, allowed values or None)} from UDLF config/*.conf"""
    conf = {}
    line_re = re.compile(r"^(?:\{\w+\})?([A-Z0-9_*]+):(STR|INT|UINT|DBL|BOL)"
                         r"(?:\((.*)\))?(?:=(.*))?$")
    for path in sorted((udlf_source / "config").glob("*.conf")):
        for line in path.read_text().splitlines():
            line = line.replace(" ", "").replace("\t", "").split("#")[0]
            if not line or line.startswith('R"') or line.startswith(")"):
                continue
            match = line_re.match(line)
            assert match, f"cannot parse {path.name}: {line}"
            allowed = match.group(3).split(";") if match.group(3) else None
            conf[match.group(1)] = (match.group(2), allowed)
    return conf


def test_every_udlf_parameter_has_a_rule(udlf_conf):
    untyped = {name for name, (kind, _) in udlf_conf.items()
               if kind != "STR" and name not in VALIDATIONS}
    assert untyped == set()


def test_rules_match_udlf_types_and_values(udlf_conf):
    for name, rule in VALIDATIONS.items():
        assert name in udlf_conf, f"{name} is not a UDLF parameter"
        kind, allowed = udlf_conf[name]
        assert RULE_TYPES[rule["type"]] == kind, name
        if rule["type"] == "enum":
            assert set(rule["values"]) == set(allowed), name


def test_method_params_cover_every_method(udlf_conf):
    methods = set(VALIDATIONS["UDL_METHOD"]["values"])
    assert set(METHOD_PARAMS) == methods
    udlf_params = {name for name in udlf_conf if name.startswith("PARAM_")}
    wrapper_params = {spec["param"] for params in METHOD_PARAMS.values()
                      for spec in params.values()}
    assert wrapper_params == udlf_params


def test_method_params_types_match_udlf(udlf_conf):
    for method, params in METHOD_PARAMS.items():
        for short, spec in params.items():
            assert PY_TYPES[spec["type"]] == udlf_conf[spec["param"]][0], spec["param"]


def test_method_defaults_are_the_bundled_config_values():
    """Defaults are the reference values of UDLF's config.ini (from the papers)."""
    config = read_config_values(str(BUNDLED_CONFIG))
    for method, params in METHOD_PARAMS.items():
        for short, spec in params.items():
            default, value = spec["default"], config[spec["param"]]
            if isinstance(default, bool):
                assert value == ("TRUE" if default else "FALSE"), spec["param"]
            elif isinstance(default, str):
                assert value == default, spec["param"]
            else:
                assert float(value) == default, spec["param"]


def test_bundled_config_is_the_udlf_reference_config(udlf_source):
    assert read_config_values(str(BUNDLED_CONFIG)) == \
        read_config_values(str(udlf_source / "bin" / "config.ini"))


def test_input_type_uses_bundled_config_by_default(monkeypatch):
    from pyUDLF import run_calls
    from pyUDLF.utils.inputType import InputType

    def no_download(*args, **kwargs):
        raise AssertionError("InputType() must not download anything")

    monkeypatch.setattr(run_calls, "verify_bin", no_download)
    inp = InputType()

    assert Path(inp.config_path) == BUNDLED_CONFIG
    assert inp.get_param("PARAM_LHRR_L")[0].strip() == "1400"
    assert not any(name.startswith("#") for name in inp.list_parameters)


@pytest.mark.parametrize("path, ok", [
    ("/data/set(copy)/rk[1];v2.txt", True),    # fine for UDLF
    ("/data/my set/rk.txt", False),            # UDLF removes spaces
    ("/data/set\t2/rk.txt", False),
    ("/data/set#2/rk.txt", False),             # UDLF cuts at '#'
])
def test_validate_path_matches_udlf_parser(path, ok):
    from pyUDLF.utils.validations import validate_path

    if ok:
        assert validate_path(path) == path
    else:
        with pytest.raises(ValueError, match="UDLF cannot read"):
            validate_path(path)
