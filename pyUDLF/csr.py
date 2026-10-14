"""
Support for UDLF-CSR (https://github.com/andreTomi/UDLF-CSR), a rewrite of
UDLF with CPRR and LHRR implemented by several engines (dense, sparse, MKL,
BLAS, Eigen) to scale to large datasets.

It is used through pyUDLF.UDLF(bin_path=..., backend="csr"). This module
knows how UDLF-CSR differs from UDLF (checked in its sources, commit b391800):

- every config variable must be declared: missing ones are not given a
  default (they are left uninitialized);
- it always exits with code 0, errors are only printed ("Execution Error:",
  "Error:", ...);
- the re-ranked lists are always written to output/reranked_lists.txt,
  relative to the working directory, which must contain an output/ folder;
  each line has the L re-ranked elements followed by the rest of the input
  line; the distance matrix (N x N) is always written to OUTPUT_FILE_PATH;
- the classes file is read by line order (names are ignored), so it must be
  in the order of the lists file;
- its log has two "EFFECTIVENESS" blocks (before, after), with P@k and
  Recall@k in percent and the MAP multiplied by 100;
- only numeric ranked lists are accepted as input (no matrix, names or
  FUSION).
"""

import re

# engine -> suffix of the UDLF-CSR method name (CPRR, CPRR_SPARSE, ...)
ENGINES = {"dense": "", "sparse": "_SPARSE", "mkl": "_MKL", "blas": "_BLAS",
           "eigen": "_EIGEN"}
METHODS = ("CPRR", "LHRR")
PINNED_COMMIT = "b391800"

# Startup error caused by a dangling pointer in VirtualArray::create (the name of
# the memory-mapped file); it happens at random (about 1-5% of the runs, every
# engine), before any computation, so the run is repeated up to RUN_ATTEMPTS times.
TRANSIENT_ERROR = "Failed to open backing file"
RUN_ATTEMPTS = 5

_ERROR_PATTERNS = [
    re.compile(r"^Execution Error: (.*)$", re.M),
    re.compile(r"^Error: (.*)$", re.M),
    re.compile(r"^(Error parsing value for key: .*)$", re.M),
    re.compile(r"^\[EventQueue\] Exception in callback: (.*)$", re.M),
    re.compile(r"^(Invalid integer found in config: .*)$", re.M),
]
_REGISTRY = re.compile(r"^Available Methods in Registry: (.*)$", re.M)
_TIME = re.compile(r"Total Execution Time: (\S+) seconds")
_METRIC = re.compile(r"^\s*(P@\d+|Recall@\d+|MAP)\s+(\S+?)%?\s*$")


def method_name(method, engine=None):
    """
    UDLF-CSR method name for a method and an engine, and the base method.

    Accepts "CPRR" with engine="sparse", or the UDLF-CSR name "CPRR_SPARSE".

    Returns:
        (base method, UDLF-CSR method), e.g. ("CPRR", "CPRR_SPARSE")

    Raises:
        ValueError: unknown method or engine, or a name that disagrees with
            the engine.
    """
    name = str(method).strip().upper()
    base, _, suffix = name.partition("_")
    if base not in METHODS:
        raise ValueError(f"UDLF-CSR implements only {list(METHODS)}, not {method!r}.")
    engine_of_name = next((e for e, s in ENGINES.items() if s == (f"_{suffix}" if suffix else "")),
                          None)
    if engine_of_name is None:
        raise ValueError(f"Unknown UDLF-CSR method {method!r}. Engines: {sorted(ENGINES)}.")
    if engine is None:
        engine = engine_of_name
    engine = str(engine).strip().lower()
    if engine not in ENGINES:
        raise ValueError(f"Unknown engine {engine!r}. Available: {sorted(ENGINES)}.")
    if suffix and engine != engine_of_name:
        raise ValueError(f"{method!r} already selects the {engine_of_name!r} engine, "
                         f"but engine={engine!r} was given.")
    return base, base + ENGINES[engine]


def check_output(output):
    """Problems reported by UDLF-CSR (it always exits with code 0)."""
    problems = []
    for pattern in _ERROR_PATTERNS:
        problems += [f"UDLF-CSR: {m.group(1).strip()}" for m in pattern.finditer(output)]
    if any(TRANSIENT_ERROR in p for p in problems):
        problems.append("This is an intermittent UDLF-CSR bug (the name of its memory-mapped "
                        "file is a dangling pointer in VirtualArray::create): run it again")
    if any("Unknown method" in p for p in problems):
        registry = available_methods(output)
        if registry:
            problems.append("This UDLF-CSR build has only: " + ", ".join(registry)
                            + " (other engines need a build with their libraries, "
                            "see scripts/build_csr.sh --full)")
    return problems


def available_methods(output):
    """Methods compiled into the binary, as listed in its output."""
    match = _REGISTRY.search(output)
    return match.group(1).split() if match else []


def parse_time(output):
    """Execution time of the method in seconds, from the UDLF-CSR output."""
    match = _TIME.search(output)
    return float(match.group(1)) if match else None


def parse_log(text):
    """
    Results of a UDLF-CSR log, as fractions (like UDLF):
    {"before": {"P@10": 0.631, ..., "MAP": 0.5471}, "after": {...}}.
    """
    blocks = [block for block in text.split("EFFECTIVENESS")[1:]]
    sections = {}
    for name, block in zip(("before", "after"), blocks):
        values = {}
        for line in block.splitlines():
            match = _METRIC.match(line)
            if match:
                values[match.group(1)] = float(match.group(2)) / 100
        sections[name] = values
    return sections


def config_text(values):
    """Config file text with every variable declared (UDLF-CSR needs all)."""
    return "".join(f"{key} = {value}\n" for key, value in values.items())
