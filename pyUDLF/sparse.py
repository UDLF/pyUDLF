"""
Support for Sparse UDLF (https://github.com/andreTomi/Sparse_UDLF), sparse
implementations of UDLF methods that scale to large datasets.

It is used through pyUDLF.UDLF(bin_path=..., backend="sparse"). This module
knows how Sparse UDLF differs from UDLF 1.70 (checked in its sources, commit
de3c14c, and by running it; see tests/test_sparse_binary.py):

- it implements CPRR, LHRR, RDPAC, RFE and BFSTREE, under the names
  CPRR_SPARSE, LHRR_SPARSE, RDPAC, RFE and BFSTree, with parameters named
  PARAM_<that name>_<parameter>; on the synthetic dataset the ranked lists are
  byte-identical to UDLF 1.70;
- it builds two binaries: bin/udlf (-ffast-math) runs CPRR and LHRR,
  bin/udlf_strict runs every method (RDPAC, RFE and BFSTree refuse fast-math);
- it reads only ranked lists of element indices (no matrices, names or FUSION);
- OUTPUT_FILE_PATH is the output file itself (UDLF 1.70 appends .txt), and the
  ranked lists are also copied to output/reranked_lists.txt in the working
  directory; the matrix output is all zeros in commit de3c14c;
- its log has "EFFECTIVENESS BEFORE/AFTER RERANKING" blocks with values x100,
  followed by a "RELATIVE GAINS" block;
- UDLF_TMPDIR sets the directory of its memory-mapped scratch files
  (default /tmp/udlf_temp).
"""

import re

PINNED_COMMIT = "de3c14c"
FAST_BINARY, STRICT_BINARY = "udlf", "udlf_strict"

# UDLF 1.70 method -> (Sparse UDLF method, binary that runs it)
METHODS = {
    "CPRR": ("CPRR_SPARSE", FAST_BINARY),
    "LHRR": ("LHRR_SPARSE", FAST_BINARY),
    "RDPAC": ("RDPAC", STRICT_BINARY),
    "RFE": ("RFE", STRICT_BINARY),
    "BFSTREE": ("BFSTree", STRICT_BINARY),
}

# Parameters Sparse UDLF adds: method -> {short name: (parameter, default, type)}
EXTRA_PARAMS = {
    "LHRR": {"threads": ("PARAM_LHRR_SPARSE_THREADS", 1, int)},
    "BFSTREE": {"b": ("PARAM_BFSTree_B", 256, int),
                "memory_budget_mb": ("PARAM_BFSTree_MEMORY_BUDGET_MB", 4096, int)},
}

# UDLF 1.70 parameters Sparse UDLF does not have, and the value they must keep
# (None: any value is ignored)
NOT_PORTED = {
    "PARAM_RFE_RERANK_BY_EMB": "FALSE",
    "PARAM_RFE_EXPORT_EMBEDDINGS": "FALSE",
    "PARAM_RFE_EMBEDDINGS_PATH": None,
    "PARAM_RFE_CCS_PATH": None,
}
# RFE with connected components (PERFORM_CCS, the UDLF default) is refused by
# Sparse UDLF de3c14c as work in progress
RFE_CCS = "PARAM_RFE_PERFORM_CCS"

# Keys of the general part of the config that Sparse UDLF knows (Validator.hpp)
GENERAL_KEYS = (
    "UDL_TASK", "UDL_METHOD", "SIZE_DATASET", "INPUT_FILE_FORMAT", "INPUT_MATRIX_TYPE",
    "INPUT_RK_FORMAT", "MATRIX_TO_RK_SORTING", "INPUT_FILE", "INPUT_FILE_LIST",
    "INPUT_FILE_CLASSES", "INPUT_IMAGES_PATH", "OUTPUT_FILE", "OUTPUT_FILE_FORMAT",
    "OUTPUT_MATRIX_TYPE", "OUTPUT_RK_FORMAT", "OUTPUT_FILE_PATH", "OUTPUT_HTML_RK_PER_FILE",
    "OUTPUT_HTML_RK_SIZE", "OUTPUT_HTML_RK_COLORS", "OUTPUT_HTML_RK_BEFORE_AFTER",
    "OUTPUT_LOG_FILE_PATH", "EFFICIENCY_EVAL", "EFFECTIVENESS_EVAL",
    "EFFECTIVENESS_COMPUTE_PRECISIONS", "EFFECTIVENESS_COMPUTE_MAP",
    "EFFECTIVENESS_COMPUTE_RECALL", "EFFECTIVENESS_RECALLS_TO_COMPUTE",
    "EFFECTIVENESS_PRECISIONS_TO_COMPUTE",
)

COMPAT_OUTPUT = "output/reranked_lists.txt"

_ERROR_PATTERNS = [
    re.compile(r"^Execution Error: (.*)$", re.M),
    re.compile(r"^Error: (.*)$", re.M),
    re.compile(r"^(Error parsing value for key: .*)$", re.M),
    re.compile(r"^(Invalid integer found in config: .*)$", re.M),
]
_REGISTRY = re.compile(r"^Available Methods in Registry: (.*)$", re.M)
_TIME = re.compile(r"Total Execution Time: (\S+) seconds")
_METRIC = re.compile(r"^\s*(P@\d+|Recall@\d+|MAP)\s+(\S+?)%?\s*$")


def method_name(method):
    """
    (UDLF method, Sparse UDLF method, binary) for a method given by its UDLF
    name ("CPRR") or its Sparse UDLF name ("CPRR_SPARSE", "BFSTree"), in any case.

    Raises:
        ValueError: a method Sparse UDLF does not implement.
    """
    name = str(method).strip().upper()
    for base, (sparse_name, binary) in METHODS.items():
        if name in (base, sparse_name.upper()):
            return base, sparse_name, binary
    raise ValueError(f"Sparse UDLF implements only {sorted(METHODS)}, not {method!r}.")


def udlf_values(values):
    """
    A Sparse UDLF config (dict of values) with the method and its parameters
    renamed to UDLF 1.70 names, for the checks shared with UDLF.
    """
    try:
        base, sparse_name, _ = method_name(values.get("UDL_METHOD", ""))
    except ValueError:
        return values
    prefix = f"PARAM_{sparse_name}_"
    renamed = {(f"PARAM_{base}_" + key[len(prefix):] if key.startswith(prefix) else key): value
               for key, value in values.items()}
    renamed["UDL_METHOD"] = base
    return renamed


def check_output(output, method=None):
    """Problems reported by Sparse UDLF in its output (stdout and stderr)."""
    problems = []
    for pattern in _ERROR_PATTERNS:
        problems += [f"Sparse UDLF: {m.group(1).strip()}" for m in pattern.finditer(output)]
    if f"Missing method parameter: {RFE_CCS}" in output:
        problems.append(f"Sparse UDLF {PINNED_COMMIT} cannot run RFE: {RFE_CCS} and the other "
                        "RFE flags are commented out in its Validator.hpp, so the config parser "
                        "drops them")
    if any("Unknown method" in p for p in problems):
        registry = available_methods(output)
        if registry:
            problems.append("This Sparse UDLF build has only: " + ", ".join(registry))
    return problems


def available_methods(output):
    """Methods compiled into the binary, as listed in its output."""
    match = _REGISTRY.search(output)
    return match.group(1).split() if match else []


def parse_time(output):
    """Execution time of the method in seconds, from the Sparse UDLF output."""
    match = _TIME.search(output)
    return float(match.group(1)) if match else None


def parse_log(text):
    """
    Measures of a Sparse UDLF log, as fractions (like UDLF):
    {"before": {"P@10": 0.631, ..., "MAP": 0.5471}, "after": {...}}.
    The "RELATIVE GAINS" block that follows is not included.
    """
    text = text.split("RELATIVE GAINS")[0]
    sections = {}
    for name, block in zip(("before", "after"), text.split("EFFECTIVENESS")[1:]):
        values = {}
        for line in block.splitlines():
            match = _METRIC.match(line)
            if match:
                values[match.group(1)] = float(match.group(2)) / 100
        sections[name] = values
    return sections


def config_text(values):
    """Config file text."""
    return "".join(f"{key} = {value}\n" for key, value in values.items())
