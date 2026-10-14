# pyUDLF

[![tests](https://github.com/UDLF/pyUDLF/actions/workflows/tests.yml/badge.svg)](https://github.com/UDLF/pyUDLF/actions/workflows/tests.yml)

**Python wrapper for [UDLF](https://github.com/UDLF/UDLF), the Unsupervised Distance Learning Framework.**

[Versão em português](READMEpt.md)

**Authors:** Gustavo Rosseto Leticio, [Lucas Pascotti Valem](http://www.lucasvalem.com) and [Daniel Carlos Guimarães Pedronette](http://www.ic.unicamp.br/~dcarlos/)

Dept. of Statistic, Applied Math. and Computing, Universidade Estadual Paulista ([UNESP](http://www.rc.unesp.br/)), Rio Claro, Brazil

----------------------
* [Overview](#overview)
* [Installation](#installation)
* [Quickstart](#quickstart)
* [Usage](#usage)
* [Running your own config file](#running-your-own-config-file)
* [Legacy API](#legacy-api)
* [Command line](#command-line)
* [File formats](#file-formats)
* [Development](#development)
* [Applications](#applications)
* [Cite](#cite)
* [Contact](#contact)
* [Acknowledgments](#acknowledgments)
* [License](#license)


## Overview

UDLF is a C++ framework of unsupervised distance learning methods for image and multimedia
retrieval: given the ranked lists (or a distance / similarity matrix) of a dataset, a method
re-ranks them using the contextual information they contain, with no labels.
pyUDLF runs these methods from Python: you pass numpy arrays (or files) and get back
the re-ranked lists and the evaluation measures (MAP, Precision@k, Recall@k) as numpy arrays
and numbers. The configuration files, input files and the UDLF binary are handled for you.

Methods (UDLF 1.70), with the names and papers listed by UDLF:

| Name in pyUDLF | Method (paper) |
|---|---|
| `CPRR` | [CPRR](http://dx.doi.org/10.1109/SIBGRAPI.2016.042) |
| `LHRR` | [LHRR](http://doi.org/10.1109/TIP.2019.2920526) |
| `RDPAC` | [RDPAC](https://doi.org/10.3390/jimaging7030049) |
| `RFE` | [RFE](https://doi.org/10.1109/TIP.2023.3268868) |
| `BFSTREE` | [BFSTree](https://doi.org/10.1016/j.patcog.2020.107666) |
| `CONTEXTRR` | [ContextRR](http://dl.acm.org/citation.cfm?id=1948207.1948291) |
| `CORGRAPH` | [Correlation Graph](http://dx.doi.org/10.1016/j.neucom.2016.03.081) |
| `RKGRAPH` | [Rk Graph Dist.](http://dx.doi.org/10.1016/j.patrec.2016.05.021) |
| `RECKNNGRAPH` | [ReckNNGraph](http://dx.doi.org/10.1016/j.imavis.2013.12.009) |
| `RLRECOM` | [RL-Recom](http://dx.doi.org/10.1145/2671188.2749336) |
| `RLSIM` | [RL-Sim*](http://dx.doi.org/10.1145/2671188.2749335) |
| `NONE` | no re-ranking (evaluates the input) |


## Installation

Requires Python 3.9+.

```bash
pip install git+https://github.com/UDLF/pyUDLF.git          # core
pip install "pyUDLF[viz] @ git+https://github.com/UDLF/pyUDLF.git"  # + ranked list images (Pillow)
```

Then install the UDLF binary (official release, checked with its SHA-256):

```bash
pyudlf download
```

It goes to `~/.pyudlf/bin` (or `$PYUDLF_HOME/bin`); `pyudlf where` shows the binary in use.
There are official builds for Linux and Windows. On other systems (e.g. macOS), build UDLF from
source (`make` in the [UDLF repository](https://github.com/UDLF/UDLF), or `scripts/build_udlf.sh`
here) and use it with `UDLF(bin_path=...)` or the `UDLF_BIN` environment variable.


## Quickstart

```python
import numpy as np
from pyUDLF import UDLF

# A small dataset: 200 elements in 10 classes, with noisy 32-D features
rng = np.random.default_rng(7)
labels = np.repeat(np.arange(10), 20)
features = rng.normal(size=(10, 32))[labels] + rng.normal(scale=1.4, size=(200, 32))

# Ranked lists: each row is a query, with all elements sorted by distance
distances = np.linalg.norm(features[:, None] - features[None], axis=2)
ranked_lists = np.argsort(distances, axis=1, kind="stable")

# Re-rank them with CPRR (needs the UDLF binary: run `pyudlf download` once)
udlf = UDLF()
res = udlf.run("CPRR", ranked_lists=ranked_lists, params={"l": 100, "k": 10},
               classes=labels)

print(res)                       # Result(method='CPRR', ranked_lists=(200, 100), MAP 0.5471 -> 0.7602)
print(res.metrics["before"]["P@10"], "->", res.metrics["after"]["P@10"])   # 0.631 -> 0.8315
before, after = res.per_query()  # average precision of each query
print((after > before).sum(), "of 200 queries improved")                  # 186 of 200 queries improved
```

This script is also in [examples/quickstart.py](examples/quickstart.py).


## Usage

The examples below continue the quickstart.

### Inputs

```python
# Ranked lists: one row per query with element indices (numpy array, list of lists or file)
res = udlf.run("LHRR", ranked_lists=ranked_lists, params={"l": 100}, classes=labels)
res = udlf.run("LHRR", ranked_lists="ranked_lists.txt", params={"l": 100}, classes=labels)

# Distance or similarity matrix (N x N)
res = udlf.run("RDPAC", matrix=distances, matrix_type="dist", params={"l": 50}, classes=labels)

# Files in the UDLF formats: ranked lists, element names ("lists") and "name:class" classes
res = udlf.run("CPRR", ranked_lists="ranked_lists.txt", names="lists.txt",
               classes="classes.txt", params={"l": 100})
```

Input files are used in place; arrays are written to a temporary directory, removed after the run.
Without `classes`, the evaluation is skipped (and a warning is logged).

### Parameters

`params` takes the parameters of the method by name; the others keep the default values of the
UDLF reference configuration. List them with `UDLF.describe`:

```python
print(UDLF.describe("CPRR"))
# CPRR parameters (params={name: value}):
#   l = 400 (int): Size of ranked lists (must be lesser than SIZE_DATASET)
#   k = 20 (int): Number of nearest neighbors
#   t = 2 (int): Number of iterations
```

`UDLF.methods()` lists the methods. Note that the default `l` of several methods (e.g. 400 or
1400) assumes larger datasets: it must not be larger than the number of elements, and the input
ranked lists must have at least `l` elements.

### Results

```python
res.ranked_lists          # re-ranked lists: numpy array (queries x output size)
res.metrics               # {"before": {...}, "after": {...}, "gain": {...}}: MAP, P@k, Recall@k
res.map_before, res.map_after
res.time                  # execution time of the method, in seconds (measured by UDLF)
res.per_query("MAP")      # value of each query, before and after (also "precision", "recall")
res.config, res.stdout    # configuration used and UDLF output, for reproducibility
```

The measures are computed by UDLF up to the size of the output ranked lists (MAP@L); `gain` is
the relative gain in percent. Other options:

```python
# Output as a distance (or similarity) matrix instead of ranked lists
res = udlf.run("CPRR", ranked_lists=ranked_lists, params={"l": 100}, output="matrix")
res.matrix.shape          # (200, 200)

# Choose the P@k / Recall@k values and keep the files of the run
res = udlf.run("CPRR", ranked_lists=ranked_lists, params={"l": 100}, classes=labels,
               precisions=[5, 10], recalls=[10], keep_files=True)
res.files                 # paths of the config, log, inputs and output of the run
```

### Fusion

```python
# Fuse ranked lists of the same dataset obtained with different features / distances
unit = features / np.linalg.norm(features, axis=1, keepdims=True)
ranked_lists_cosine = np.argsort(-(unit @ unit.T), axis=1, kind="stable")
res = udlf.fuse("CPRR", [ranked_lists, ranked_lists_cosine], params={"l": 100}, classes=labels)
res.map_after             # FUSION results only have metrics after fusion
```

### UDLF-CSR

[UDLF-CSR](https://github.com/andreTomi/UDLF-CSR) is a rewrite of UDLF that runs CPRR and LHRR
with several engines (`dense`, `sparse`, `mkl`, `blas`, `eigen`) to scale to large datasets.
It has no official build: compile it (`scripts/build_csr.sh` builds the `dense` and `sparse`
engines; `scripts/build_csr.sh --full` builds all of them and needs Intel MKL, GraphBLAS and
Eigen) and pass its path with `bin_path=` or the `UDLF_CSR_BIN` environment variable.

```python
csr = UDLF(backend="csr", threads=1)      # binary from UDLF_CSR_BIN
res = csr.run("CPRR", ranked_lists=ranked_lists, params={"l": 100, "k": 10},
              classes=labels, engine="sparse")
print(res)   # Result(method='CPRR_SPARSE', ranked_lists=(200, 100), MAP 0.5471 -> 0.7633)
res.warnings                              # problems found in the results (see below)
res.raw_metrics                           # measures computed by UDLF-CSR itself
```

The result is the same `Result` as with UDLF. `metrics` are computed by pyUDLF with the UDLF
definitions, so UDLF and UDLF-CSR results are directly comparable (UDLF-CSR averages the recall
per query, not per class). UDLF-CSR only takes ranked lists of element indices (no matrix,
names or fusion); `output="matrix"` gives its distance matrix. Behaviors of UDLF-CSR (commit
`b391800`) handled by pyUDLF:

- the `sparse` engines return ranked lists with repeated elements, which inflates the measures:
  reported in `res.warnings`;
- the `dense` engines give slightly different results from run to run with several threads:
  use `threads=1` for reproducible results;
- an intermittent startup error ("Failed to open backing file") is retried automatically and
  reported in `res.warnings`.

### Errors

Problems are reported as exceptions, before running UDLF whenever possible:

```python
from pyUDLF import UDLFParamError

try:
    udlf.run("CPRR", ranked_lists=ranked_lists, params={"l": 500})
except UDLFParamError as e:
    print(e)   # PARAM_CPRR_L = 500 is larger than the dataset (N = 200). Pass a smaller value in params.
```

`UDLFParamError` (invalid method, parameter or input), `UDLFRunError` (UDLF failed: has
`.problems`, `.output` and `.config`) and `UDLFNotFoundError` (no binary) all derive from
`UDLFError`. Warnings and errors are logged with the standard `logging` module; call
`pyUDLF.enable_logging("INFO")` to also see informative messages.


## Running your own config file

A UDLF configuration file runs as it is. Relative paths are relative to the current directory:

```python
res = udlf.run_config("config.ini")
res.ranked_lists, res.metrics, res.files
```


## Legacy API

The API of previous versions (`InputType` and `run_calls`) is still available and gives the same
results. The [wiki](https://github.com/UDLF/pyUDLF/wiki/Documentation) documents it.

```python
from pyUDLF import run_calls
from pyUDLF.utils.inputType import InputType

inp = InputType()                      # starts from the UDLF reference configuration
inp.set_method_name("CPRR")
inp.set_input_file("ranked_lists.txt")
inp.set_lists_file("lists.txt")
inp.set_classes_file("classes.txt")
inp.set_dataset_size(200)
inp.set_method_parameters("CPRR", l=100, k=10)
inp.set_output_file_format("RK")
inp.set_output_rk_format("NUM")
inp.set_output_file_path("output")     # writes output.txt
inp.set_output_log_file_path("log.txt")

output = run_calls.run(inp, get_output=True)
print(output.log_dict["MAP"])   # {'Before': 0.5471, 'After': 0.7602, 'Gain': 38.9512}
```

See the [CHANGELOG](CHANGELOG.md) for the behavior changes of this version.


## Command line

```bash
pyudlf download              # install the official UDLF binary (--version, --dest, --force)
pyudlf where                 # binary used by pyUDLF
pyudlf methods               # available methods
pyudlf describe CPRR         # parameters of a method
```


## File formats

These are the formats UDLF reads (see the [UDLF wiki](https://github.com/UDLF/UDLF/wiki/File-Formats)):

- **Ranked lists**: one line per query, elements separated by spaces, either as indices
  (`0 12 25 ...`) or as names (`img_0001.jpg img_0013.jpg ...`, then pass `names=`).
  Each line must have at least `l` elements; the query is usually the first one.
- **Matrix**: N lines with N values (distances or similarities) separated by spaces.
- **Lists** (`names=`): one element name per line, in the order of the dataset.
- **Classes** (`classes=`): one `name:class` per line.

UDLF cannot read paths with spaces or `#` in its configuration files, so pyUDLF rejects them.


## Development

```bash
git clone https://github.com/UDLF/pyUDLF.git && cd pyUDLF
python3 -m venv .venv && .venv/bin/pip install -e ".[viz,test]"
scripts/build_udlf.sh            # builds UDLF 1.70 from source into .udlf/ (used by the tests)
.venv/bin/python -m pytest
```

The tests compare every pyUDLF run with UDLF executed directly on the same configuration, using
the synthetic dataset in `tests/data/synthetic`. GitHub Actions runs them on every push and pull
request (`.github/workflows/tests.yml`): Linux with Python 3.9 to 3.13, the built package, and
Windows / macOS.


## Applications

The methods available in the pyUDLF framework have been utilized in a variety of multimedia and machine-learning scenarios. Among them:
- Image and Video Retrieval
- Person Re-ID
- Weakly Supervised Classification
- Clustering


## Cite
If you use this software, please cite

 ```latex
@inproceedings{pyUDLF,
    author = {Gustavo Leticio and Lucas Pascotti Valem and Leonardo Tadeu Lopes and Daniel Carlos Guimar\~{a}es Pedronette},
    title = {PyUDLF: A Python Framework for Unsupervised Distance Learning Tasks},
    year = {2023},
    isbn = {9798400701085},
    publisher = {Association for Computing Machinery},
    address = {New York, NY, USA},
    url = {https://doi.org/10.1145/3581783.3613466},
    doi = {10.1145/3581783.3613466},
    booktitle = {Proceedings of the 31st ACM International Conference on Multimedia},
    pages = {9680–9684},
    numpages = {5},
    series = {MM '23}
}
```

## Contact
**Gustavo Rosseto Leticio**: `gustavo.leticio@gmail.com` or `gustavo.leticio@unesp.br`

**Lucas Pascotti Valem**: `lucaspascottivalem@gmail.com` or `lucas.valem@unesp.br`

**Daniel Carlos Guimarães Pedronette**: `daniel.pedronette@unesp.br`


## Acknowledgments

The authors are grateful to São Paulo Research Foundation – FAPESP (grants 2013/08645-0, 2014/04220-8, 2018/15597-6) and Brazilian National Council for Scientific and Technological Development – CNPq (grants 309439/2020-5 and 422667/2021-8).


## License

This project is licensed under GPLv2. See [details.](https://github.com/UDLF/pyUDLF/blob/main/LICENSE)
