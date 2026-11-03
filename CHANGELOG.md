# Changelog

## 0.9.0 (unreleased)

Targets UDLF 1.70. Every pyUDLF run is tested against UDLF executed directly on the same
configuration (12 methods, all input/output formats, fusion), on a synthetic dataset shipped in
`tests/data/synthetic`.

### Added
- High-level API: `pyUDLF.UDLF` with `run()`, `fuse()`, `run_config()`, `methods()` and
  `describe()`. Inputs as numpy arrays or files; results (`Result`) with numpy outputs, metrics
  as floats, `per_query()` values that reproduce the MAP of the UDLF log, the config used and
  the UDLF output. Errors are exceptions: `UDLFParamError`, `UDLFRunError`, `UDLFNotFoundError`.
- `pyudlf` command (also `python -m pyUDLF`): `download`, `where`, `methods`, `describe`.
- `pyUDLF.install.download_udlf()`: installs the official UDLF release over https, pinned to a
  version and checked with its SHA-256. `PYUDLF_HOME` changes the installation directory.
- The UDLF 1.70 reference `config.ini` is shipped with pyUDLF and is the default template of
  `InputType` (the defaults no longer depend on a downloaded file).
- `pyUDLF.enable_logging(level)`.
- Sparse UDLF backend: `UDLF(bin_path=..., backend="sparse")` runs CPRR, LHRR, RDPAC, RFE and
  BFSTREE of [Sparse UDLF](https://github.com/andreTomi/Sparse_UDLF), sparse implementations for
  large datasets, and returns the same `Result`, with measures computed with the UDLF
  definitions (Sparse UDLF's own in `raw_metrics`). On the synthetic dataset its ranked lists
  are byte-identical to UDLF 1.70. `bin_path` (or `UDLF_SPARSE_BIN`) is the directory of its two
  binaries; each method runs in the one that supports it. Its extra parameters are `threads`
  (LHRR) and `b`, `memory_budget_mb` (BFSTREE). `scripts/build_sparse.sh` builds it (pinned to
  commit `de3c14c`), also without root: it uses the compiler and libraries of an active conda
  environment (`CXX`, `CONDA_PREFIX`), and builds with `-std=gnu++17` when the compiler has no
  C++23 (g++ < 11). The binary type is checked: a UDLF binary used as Sparse UDLF (or the
  opposite), or a binary of its predecessor UDLF-CSR, is reported. `backend="csr"` and
  `UDLF_CSR_BIN` are aliases.
- `UDLF(threads=...)` sets the number of threads of the binary (`OMP_NUM_THREADS`).
- `Result.warnings`: problems found in the results.
- In-memory ranked lists as numpy arrays in `InputType.set_input_files`.
- `pyproject.toml` packaging and a test suite (`pytest`).
- `examples/`: runnable scripts (quickstart, comparing methods, parameter search, input formats,
  fusion, per-query analysis, your own data from the command line, Sparse UDLF, legacy API),
  all run by the tests.
- Continuous integration (GitHub Actions): Linux with Python 3.9 to 3.13, the built package
  with the official UDLF release, Windows (official UDLF release) and macOS (UDLF built from
  source).

### Changed (legacy API)
- `run()` / `runWithConfig()` decide whether UDLF failed from its return code and from the
  messages UDLF prints when it replaces a value by its default, instead of searching words such
  as "error" in its output. Runs that used to "succeed" with wrong results now return `False`
  with the reason in the log; paths containing words like "error" no longer make a run fail.
- Inputs are checked before running: ranked lists shorter than the number of elements the method
  reads per line (`L`), or with fewer lines than `SIZE_DATASET`, are rejected. UDLF silently
  read across lines in this case (or crashed).
- `log_dict` / `get_log()` values are numbers: `{"Before": 0.5471, "After": 0.7602,
  "Gain": 38.95}` (gain in percent), `"Time"` in seconds. They were strings such as `'27.6%'`.
- `set_method_parameters()` changes only the parameters given; `reset_defaults=True` keeps the
  previous behavior (reset the others to their defaults). Unknown names raise `ValueError`;
  ints are accepted for float parameters.
- `set_param()` validates and normalizes known parameters, and raises `KeyError` for a parameter
  that does not exist (use `add_new_parameter()`).
- `setBinaryPath()` / `setConfigPath()` raise `FileNotFoundError` for a missing file instead of
  silently using the default path.
- The `UDLF_BIN` environment variable sets the binary of the legacy API too (as in `pyUDLF.UDLF`).
- `evaluation.compute_map()` divides the average precision by `min(depth, class size)` and
  `compute_recall()` averages per class, as UDLF; values differ from 0.8 when the depth is
  smaller than a class, or (recall) when classes have different sizes.
- `readData.read_classes()` returns string labels when they are not numeric (it failed before).
- No handlers are installed on the loggers: warnings and errors are still shown, informative
  messages are hidden (see `enable_logging`). Internal `print`s were replaced by logging.
- The binary is downloaded over https from the official GitHub release and checked with its
  SHA-256 (was a plain http redirect, not checked).

### Fixed
- Packaging: `pip install` did not install the dependencies (numpy, Pillow), so the package could
  not be imported. Pillow is now optional (`pip install "pyUDLF[viz]"`); `requests` was removed.
- `OUTPUT_RK_FORMAT = ALL` (the template default): the output was read from `<path>.txt`
  instead of `<path>_num.txt`. The output path also depended on the order of the config lines.
- Individual gain: raised `IndexError` whenever the output lists were shorter than the dataset,
  and failed with string class labels. `get_individual_gain_list()` returned nested tuples.
- In-memory ranked lists (`list[list]`) raised `TypeError`.
- FUSION with more than two files: `NUM_INPUT_FUSION_FILES` was not updated, so UDLF ignored
  the extra files.
- `PARAM_RFE_TH_CC` and `PARAM_RDPAC_L_MULT` are decimals in UDLF (were validated as ints);
  `NONE` was missing from `set_method_parameters()`.
- `compute_recall()` returned 0 with the default depth; evaluation defaults used the number of
  queries as depth; evaluation is vectorized (much faster).
- Comment lines of the config were read as parameters; `#` in paths is rejected and parentheses
  are accepted (matching what UDLF can read).
- Visualization: the list and classes files were checked as directories.
- `gridSearch`: failed runs were ranked first, `EFFECTIVENESS_COMPUTE_* = FALSE` was ignored,
  and `find_best_method_with_best_k` used a fixed ranked list size of 280.
- Windows: the official archive (`.tar.gz`) was opened as a zip, so the download never worked;
  the binary is now run directly (not through `cmd /c`).

### Removed
- `setup.py`, `requirements.txt`, `install.sh` and the empty `PKG-INFO`.

### Open questions
- Defaults of `PARAM_NONE_L`, `PARAM_LHRR_L` and `PARAM_BFSTREE_L`: the `config.ini` inside the
  UDLF 1.70 release has 1000, the one in the UDLF repository (tag v1.70) has 1400. pyUDLF uses
  1400 (the repository value, also the previous `set_method_parameters()` default).
- Sparse UDLF (commit `de3c14c`), to report upstream; pyUDLF detects or works around them:
  - RFE cannot run: `PARAM_RFE_PERFORM_CCS`, `PARAM_RFE_RERANK_BY_EMB` and
    `PARAM_RFE_EXPORT_EMBEDDINGS` are read by `RFE.hpp` but commented out in `Validator.hpp`,
    so the config parser drops them ("Missing method parameter"); the error explains it;
  - RFE with connected components (`perform_ccs=True`, the UDLF default) is refused as work in
    progress: pyUDLF runs RFE with `perform_ccs=False` and warns;
  - the matrix output (`OUTPUT_FILE_FORMAT = MATRIX`) is all zeros, and the log then evaluates
    the input as "after": `output="matrix"` is refused, `run_config` warns;
  - the ranked lists are always also written to `output/reranked_lists.txt` in the working
    directory (pyUDLF runs it in the run directory);
  - building needs jemalloc (`scripts/build_sparse.sh` links the runtime library when the
    development package is missing), and the `make test-*` targets need directories that are
    not in the repository.

## 0.8

Last version before this changelog.
