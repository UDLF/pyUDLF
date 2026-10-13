"""
High-level API of pyUDLF: run UDLF methods on numpy arrays (or files) and get
the results back as numpy arrays and numbers.

    from pyUDLF import UDLF

    udlf = UDLF()
    res = udlf.run("CPRR", ranked_lists=rks, params={"k": 20}, classes=labels)
    res.ranked_lists, res.map_after

The files UDLF needs (config, lists, classes, inputs) are written to a
temporary directory, removed after the run unless keep_files=True.
"""

import logging
import os
import re
import shutil
import tempfile
from pathlib import Path

import numpy as np

from pyUDLF import run_calls
from pyUDLF.errors import UDLFError, UDLFNotFoundError, UDLFParamError, UDLFRunError
from pyUDLF.utils import evaluation, parser, readData
from pyUDLF.utils.validations import (METHOD_PARAMS, VALIDATIONS, matches_type,
                                      validate_param, validate_path)

logger = logging.getLogger(__name__)

# Reference values of the UDLF config shipped with pyUDLF (UDLF v1.70)
_TEMPLATE = parser.read_config_values(run_calls.bundled_config_path)

# Methods whose UDLF implementation aborts in FUSION tasks
_NO_FUSION = {"NONE", "BFSTREE", "RLRECOM"}

_MEASURES = {"MAP": evaluation.compute_map,
             "PRECISION": evaluation.compute_precision,
             "RECALL": evaluation.compute_recall}


class Result:
    """
    Results of a UDLF run.

    Attributes:
        method (str): UDLF method.
        ranked_lists (np.ndarray | None): re-ranked lists (queries x L), int32.
        matrix (np.ndarray | None): output matrix (N x N), when output="matrix".
        metrics (dict): {"before": {...}, "after": {...}, "gain": {...}} with
            "MAP", "P@k" and "Recall@k" values ("gain" in percent). Empty when
            the run had no classes. FUSION runs only have "after".
        time (float | None): execution time of the method, measured by UDLF (s).
        config (str): text of the config file used.
        stdout (str): everything UDLF printed.
        files (dict): paths of the files of the run, when they were kept.
    """

    def __init__(self, method, *, ranked_lists=None, matrix=None, metrics=None,
                 time=None, config="", stdout="", files=None, evaluation_data=None):
        self.method = method
        self.ranked_lists = ranked_lists
        self.matrix = matrix
        self.metrics = metrics or {}
        self.time = time
        self.config = config
        self.stdout = stdout
        self.files = files or {}
        self._evaluation_data = evaluation_data

    @property
    def map_before(self):
        return self.metrics.get("before", {}).get("MAP")

    @property
    def map_after(self):
        return self.metrics.get("after", {}).get("MAP")

    def per_query(self, measure="MAP", depth=None):
        """
        Value of a measure for each query, before and after the method.

        Averaging them gives the values in `metrics` (as computed by UDLF).

        Args:
            measure (str): "MAP", "PRECISION" or "RECALL".
            depth (int, optional): positions considered; default: the size of
                the output ranked lists (as UDLF does for the MAP).

        Returns:
            (np.ndarray, np.ndarray): values before and after, one per query.
        """
        if self._evaluation_data is None:
            raise UDLFError("per_query needs a UDL run (not FUSION) with classes and "
                            "ranked lists as output.")
        if measure.upper() not in _MEASURES:
            raise UDLFParamError(f"Unknown measure {measure!r}. "
                                 f"Use one of {sorted(_MEASURES)}.")
        before, after, classes = self._evaluation_data()
        depth = depth or after.shape[1]
        function = _MEASURES[measure.upper()]
        _, values_before = function(before, classes, depth)
        _, values_after = function(after, classes, depth)
        return np.asarray(values_before), np.asarray(values_after)

    def __repr__(self):
        parts = [f"method={self.method!r}"]
        if self.ranked_lists is not None:
            parts.append(f"ranked_lists={self.ranked_lists.shape}")
        if self.matrix is not None:
            parts.append(f"matrix={self.matrix.shape}")
        if self.map_after is not None:
            if self.map_before is not None:
                parts.append(f"MAP {self.map_before:.4f} -> {self.map_after:.4f}")
            else:
                parts.append(f"MAP {self.map_after:.4f}")
        return f"Result({', '.join(parts)})"


class UDLF:
    """
    Runs UDLF methods.

    Args:
        bin_path (str, optional): path of the UDLF binary. Default: the
            UDLF_BIN environment variable, then ~/.pyudlf/bin/udlf.
        workdir (str, optional): directory for the files of each run (kept).
            Default: a new temporary directory per run, removed at the end
            unless keep_files=True.
    """

    def __init__(self, bin_path=None, workdir=None):
        self.bin_path = _find_binary(bin_path)
        self.workdir = workdir

    # ------------------------------------------------------------------ info

    @staticmethod
    def methods():
        """Names of the available methods."""
        return sorted(METHOD_PARAMS)

    @staticmethod
    def describe(method):
        """Parameters of a method, with their default values and descriptions."""
        method = _check_method(method)
        comments = readData.read_config(run_calls.bundled_config_path)[0]
        lines = [f"{method} parameters (params={{name: value}}):"]
        for name, spec in METHOD_PARAMS[method].items():
            comment = comments.get(spec["param"], ["", ""])
            text = comment[1].strip() if len(comment) > 1 else ""
            text = re.sub(r"^\([^)]*\):?\s*", "", text)  # drop the "(TUint):" prefix
            rule = VALIDATIONS.get(spec["param"], {})
            if rule.get("type") == "enum":
                text += f" [one of: {', '.join(sorted(rule['values']))}]"
            lines.append(f"  {name} = {spec['default']!r} ({spec['type'].__name__})"
                         + (f": {text.strip()}" if text.strip() else ""))
        return "\n".join(lines)

    # ------------------------------------------------------------------ runs

    def run(self, method, *, ranked_lists=None, matrix=None, matrix_type="dist",
            params=None, classes=None, names=None, precisions=None, recalls=None,
            output="ranked_lists", output_matrix_type="dist", keep_files=False):
        """
        Run a UDLF method on one input (UDL task).

        Args:
            method (str): method name, see methods().
            ranked_lists: ranked lists, one row per query, with the indices of
                the elements (2D numpy array or list of lists), or the path of a
                ranked lists file (numeric, or with names: then pass names=).
            matrix: distance or similarity matrix (N x N numpy array) or the
                path of a matrix file. Use either ranked_lists or matrix.
            matrix_type (str): "dist" or "sim", type of the input matrix.
            params (dict, optional): method parameters by name (see describe());
                the others keep the default values of the UDLF config.
            classes (optional): class label of each element (sequence of N
                labels), or the path of a UDLF classes file ("name:class" per
                line, then pass names=). Enables the effectiveness evaluation.
            names (optional): names of the elements (sequence) or the path of
                a UDLF lists file. Needed for files that refer to names.
            precisions, recalls (optional): k values of P@k and Recall@k.
                Default: those of the UDLF config not larger than the output.
            output (str): "ranked_lists" or "matrix".
            output_matrix_type (str): "dist" or "sim", when output="matrix".
            keep_files (bool): keep the files of the run (see Result.files).

        Returns:
            Result

        Raises:
            UDLFParamError: invalid method, parameter or input.
            UDLFRunError: UDLF failed.
        """
        method = _check_method(method)
        if (ranked_lists is None) == (matrix is None):
            raise UDLFParamError("Pass exactly one of ranked_lists= or matrix=.")
        with _RunDir(self.workdir, keep_files) as (work, kept):
            if ranked_lists is not None:
                source = _prepare_ranked_lists(ranked_lists, work / "input.txt")
            else:
                source = _prepare_matrix(matrix, matrix_type, work / "input.txt")
            return self._execute(method, "UDL", [source], work, kept, params, classes,
                                 names, precisions, recalls, output, output_matrix_type)

    def fuse(self, method, inputs, *, params=None, classes=None, names=None,
             precisions=None, recalls=None, output="ranked_lists",
             output_matrix_type="dist", keep_files=False):
        """
        Fuse several ranked lists of the same dataset with a UDLF method
        (FUSION task). Accepts the same arguments as run(), except that the
        input is `inputs`, a list of ranked lists (arrays or file paths).

        Returns:
            Result (FUSION results have metrics only after fusion)
        """
        method = _check_method(method)
        if method in _NO_FUSION:
            raise UDLFParamError(f"{method} does not support FUSION in UDLF. Fusion "
                                 f"methods: {sorted(set(METHOD_PARAMS) - _NO_FUSION)}")
        if not isinstance(inputs, (list, tuple)) or len(inputs) < 2:
            raise UDLFParamError("fuse() needs a list with at least two inputs.")
        with _RunDir(self.workdir, keep_files) as (work, kept):
            sources = [_prepare_ranked_lists(value, work / f"input_{i}.txt")
                       for i, value in enumerate(inputs, 1)]
            if len({s.rk_format for s in sources}) > 1:
                raise UDLFParamError("All fusion inputs must have the same format "
                                     "(numeric indices or names).")
            return self._execute(method, "FUSION", sources, work, kept, params, classes,
                                 names, precisions, recalls, output, output_matrix_type)

    def run_config(self, config_path):
        """
        Run UDLF with an existing config file, as it is.

        Relative paths in the config are relative to the current directory,
        as when running the UDLF binary by hand.

        Returns:
            Result with the outputs the config declares.
        """
        config_path = os.path.abspath(os.path.expanduser(str(config_path)))
        if not os.path.isfile(config_path):
            raise UDLFParamError(f"Config file not found: {config_path}")
        input_problems = run_calls.check_input_files(config_path)
        if input_problems:
            raise UDLFParamError("; ".join(input_problems))

        output, problems = run_calls.execute_udlf(config_path, self.bin_path)
        config_text = Path(config_path).read_text()
        if problems:
            raise UDLFRunError(problems, output, config_text)

        values = parser.read_config_values(config_path)
        paths = parser.parse_config(config_path)
        n = int(values.get("SIZE_DATASET", 0))
        ranked_lists = matrix = None
        if paths["rk_path"] and os.path.isfile(paths["rk_path"]):
            text_rks = paths["out_rk_format"] == "STR"
            ranked_lists = _read_matrix(paths["rk_path"], n, str if text_rks else np.int32)
        if paths["matrix_path"] and os.path.isfile(paths["matrix_path"]):
            matrix = _read_matrix(paths["matrix_path"], n, np.float64)

        evaluation_data = None
        if (values.get("EFFECTIVENESS_EVAL", "TRUE") == "TRUE" and paths["task"] == "UDL"
                and paths["in_file_format"] == "RK" and paths["in_rk_format"] == "NUM"
                and ranked_lists is not None and paths["out_rk_format"] != "STR"):
            def evaluation_data(rks=ranked_lists, p=paths):
                before = np.array(_read_top(p["before_path"], rks.shape[1]), dtype=np.int64)
                return before, rks, readData.read_classes(p["list_path"], p["classes_path"])

        files = {key: paths[path_key] for key, path_key in
                 [("ranked_lists", "rk_path"), ("matrix", "matrix_path"), ("log", "log_path")]
                 if paths[path_key]}
        files["config"] = config_path
        log = readData.parse_log(output)
        return Result(values.get("UDL_METHOD", ""), ranked_lists=ranked_lists, matrix=matrix,
                      metrics=_metrics(log, paths["task"]), time=log.get("Time"),
                      config=config_text, stdout=output, files=files,
                      evaluation_data=evaluation_data)

    # ------------------------------------------------------------- internals

    def _execute(self, method, task, sources, work, kept, params, classes, names,
                 precisions, recalls, output, output_matrix_type):
        n = sources[0].n
        if any(s.n != n for s in sources):
            raise UDLFParamError(f"All inputs must have the same number of rows: "
                                 f"{[s.n for s in sources]}")
        if output not in ("ranked_lists", "matrix"):
            raise UDLFParamError("output must be 'ranked_lists' or 'matrix'.")
        output_matrix_type = _check_choice(output_matrix_type, ("dist", "sim"),
                                           "output_matrix_type")

        method_values = _method_params(method, params)
        out_size = run_calls._required_columns(dict(method_values, UDL_METHOD=method,
                                                    SIZE_DATASET=str(n)))
        _check_sizes(method, method_values, n)

        names_path, names_list = _prepare_names(names, n, work / "lists.txt")
        if any(s.rk_format == "STR" for s in sources) and names is None:
            raise UDLFParamError("Ranked lists with element names need names= "
                                 "(the names of the elements, in order).")
        classes_path, classes_list = _prepare_classes(classes, names, names_list,
                                                      work / "classes.txt")
        evaluate = classes_path is not None
        if not evaluate:
            logger.warning("No classes given: effectiveness evaluation is disabled.")
        precisions = _measure_depths(precisions, "EFFECTIVENESS_PRECISIONS_TO_COMPUTE",
                                     out_size, "precisions")
        recalls = _measure_depths(recalls, "EFFECTIVENESS_RECALLS_TO_COMPUTE",
                                  out_size, "recalls")

        config = {
            "UDL_TASK": task,
            "UDL_METHOD": method,
            "SIZE_DATASET": n,
            "INPUT_FILE_FORMAT": sources[0].file_format,
            "INPUT_MATRIX_TYPE": sources[0].matrix_type,
            "INPUT_RK_FORMAT": sources[0].rk_format,
            "MATRIX_TO_RK_SORTING": _TEMPLATE["MATRIX_TO_RK_SORTING"],
            "NUM_INPUT_FUSION_FILES": len(sources) if task == "FUSION" else 0,
        }
        if task == "FUSION":
            for i, source in enumerate(sources, 1):
                config[f"INPUT_FILES_FUSION_{i}"] = source.path
        config.update({
            "INPUT_FILE": sources[0].path,
            "INPUT_FILE_LIST": names_path,
            "INPUT_FILE_CLASSES": classes_path or _TEMPLATE["INPUT_FILE_CLASSES"],
            "INPUT_IMAGES_PATH": _TEMPLATE["INPUT_IMAGES_PATH"],
            "OUTPUT_FILE": "TRUE",
            "OUTPUT_FILE_FORMAT": "MATRIX" if output == "matrix" else "RK",
            "OUTPUT_MATRIX_TYPE": output_matrix_type,
            "OUTPUT_RK_FORMAT": "NUM",
            "OUTPUT_FILE_PATH": str(work / "output"),
            "OUTPUT_HTML_RK_PER_FILE": _TEMPLATE["OUTPUT_HTML_RK_PER_FILE"],
            "OUTPUT_HTML_RK_SIZE": _TEMPLATE["OUTPUT_HTML_RK_SIZE"],
            "OUTPUT_HTML_RK_COLORS": _TEMPLATE["OUTPUT_HTML_RK_COLORS"],
            "OUTPUT_HTML_RK_BEFORE_AFTER": _TEMPLATE["OUTPUT_HTML_RK_BEFORE_AFTER"],
            "OUTPUT_LOG_FILE_PATH": str(work / "log.txt"),
            "EFFICIENCY_EVAL": "TRUE",
            "EFFECTIVENESS_EVAL": _bool(evaluate),
            "EFFECTIVENESS_COMPUTE_PRECISIONS": _bool(evaluate and bool(precisions)),
            "EFFECTIVENESS_COMPUTE_MAP": _bool(evaluate),
            "EFFECTIVENESS_COMPUTE_RECALL": _bool(evaluate and bool(recalls)),
            "EFFECTIVENESS_PRECISIONS_TO_COMPUTE": ",".join(map(str, precisions or [1])),
            "EFFECTIVENESS_RECALLS_TO_COMPUTE": ",".join(map(str, recalls or [1])),
        })
        config.update(method_values)
        config_text = "".join(f"{key} = {value}\n" for key, value in config.items())
        config_path = work / "config.ini"
        config_path.write_text(config_text)

        input_problems = run_calls.check_input_files(str(config_path))
        if input_problems:
            raise UDLFParamError("; ".join(input_problems))

        stdout, problems = run_calls.execute_udlf(str(config_path), self.bin_path,
                                                  cwd=str(work))
        if problems:
            raise UDLFRunError(problems, stdout, config_text)

        log = readData.parse_log(stdout)
        output_path = work / "output.txt"
        ranked_lists = matrix = None
        if output == "matrix":
            matrix = _read_matrix(output_path, n, np.float64)
        else:
            ranked_lists = _read_matrix(output_path, n, np.int32)

        evaluation_data = None
        if evaluate and task == "UDL" and ranked_lists is not None:
            before_source = sources[0]

            def evaluation_data(rks=ranked_lists):
                return before_source.ranked_lists(rks.shape[1], names_list), rks, classes_list

        files = {}
        if kept:
            files = {"config": str(config_path), "log": str(work / "log.txt"),
                     "lists": names_path, "output": str(output_path)}
            if classes_path:
                files["classes"] = classes_path
        return Result(method, ranked_lists=ranked_lists, matrix=matrix,
                      metrics=_metrics(log, task), time=log.get("Time"),
                      config=config_text, stdout=stdout, files=files,
                      evaluation_data=evaluation_data)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

class _RunDir:
    """Directory of the files of one run: removed at the end unless kept."""

    def __init__(self, workdir, keep_files):
        self.workdir = workdir
        self.keep = keep_files or workdir is not None

    def __enter__(self):
        if self.workdir is not None:
            path = Path(os.path.expanduser(str(self.workdir))).resolve()
            path.mkdir(parents=True, exist_ok=True)
        else:
            path = Path(tempfile.mkdtemp(prefix="pyudlf_"))
        self.path = path
        try:
            _check_path(str(path))
        except UDLFParamError:
            self.__exit__(None, None, None)
            raise
        return path, self.keep

    def __exit__(self, *exc):
        if not self.keep:
            shutil.rmtree(self.path, ignore_errors=True)
        elif exc[0] is None:
            logger.info("Files of the run kept in %s", self.path)
        return False


class _Source:
    """An input of a run: a file UDLF reads, plus how to read it back."""

    def __init__(self, path, n, file_format, rk_format="NUM", matrix_type="DIST",
                 array=None):
        self.path = path
        self.n = n
        self.file_format = file_format
        self.rk_format = rk_format
        self.matrix_type = matrix_type
        self.array = array

    def ranked_lists(self, depth, names):
        """Input ranked lists (top `depth`), as indices, for the evaluation."""
        if self.file_format == "MATRIX":
            matrix = self.array if self.array is not None else _read_matrix(
                self.path, self.n, np.float64)
            order = matrix if self.matrix_type == "DIST" else -matrix
            return np.argsort(order, axis=1, kind="stable")[:, :depth]
        if self.array is not None:
            return self.array[:, :depth]
        rows = _read_top(self.path, depth)
        if self.rk_format == "STR":
            index = {name: i for i, name in enumerate(names)}
            return np.array([[index[x] for x in row] for row in rows])
        return np.array(rows, dtype=np.int64)


def _find_binary(bin_path):
    if bin_path is not None:
        path, origin = os.path.expanduser(str(bin_path)), "bin_path"
    elif os.environ.get("UDLF_BIN"):
        path, origin = os.path.expanduser(os.environ["UDLF_BIN"]), "UDLF_BIN"
    else:
        path, origin = run_calls.bin_path, "default location"
    if not os.path.isfile(path):
        raise UDLFNotFoundError(
            f"UDLF binary not found at {path} ({origin}). Build it with "
            "scripts/build_udlf.sh (in the pyUDLF repository), or download a release "
            "from https://github.com/UDLF/UDLF/releases, then pass bin_path= or set "
            "the UDLF_BIN environment variable.")
    return path


def _check_method(method):
    name = str(method).strip().upper()
    if name not in METHOD_PARAMS:
        raise UDLFParamError(f"Unknown method {method!r}. Available: {sorted(METHOD_PARAMS)}")
    return name


def _check_choice(value, choices, name):
    if str(value).lower() not in choices:
        raise UDLFParamError(f"{name} must be one of {choices}, got {value!r}.")
    return str(value).upper()


def _check_path(path):
    try:
        return validate_path(path)
    except ValueError as e:
        raise UDLFParamError(str(e)) from None


def _bool(value):
    return "TRUE" if value else "FALSE"


def _format_value(value):
    if isinstance(value, (bool, np.bool_)):
        return _bool(value)
    return str(value)


def _method_params(method, params):
    """Values of all the parameters of a method: defaults + params, validated."""
    specs = METHOD_PARAMS[method]
    by_full_name = {spec["param"]: short for short, spec in specs.items()}
    values = {spec["param"]: spec["default"] for spec in specs.values()}
    for key, value in (params or {}).items():
        short = str(key).lower()
        if short not in specs:
            short = by_full_name.get(str(key).upper())
        if short is None:
            raise UDLFParamError(f"Unknown parameter {key!r} for {method}. "
                                 f"Valid names: {sorted(specs)}")
        spec = specs[short]
        if not matches_type(value, spec["type"]):
            raise UDLFParamError(f"Parameter {short!r} of {method} must be "
                                 f"{spec['type'].__name__}, got {type(value).__name__}.")
        try:
            validate_param(spec["param"], value)
        except ValueError as e:
            raise UDLFParamError(str(e)) from None
        values[spec["param"]] = value
    return {name: _format_value(value) for name, value in values.items()}


def _check_sizes(method, values, n):
    """Sizes that UDLF does not accept (or does not check) for N elements."""
    for name, value in values.items():
        if name.endswith(("_L", "_CK")) and method != "RDPAC" and int(value) > n:
            raise UDLFParamError(f"{name} = {value} is larger than the dataset (N = {n}). "
                                 f"Pass a smaller value in params.")


def _measure_depths(values, config_name, out_size, name):
    """k values of P@k / Recall@k: given ones are checked, defaults filtered."""
    if values is None:
        defaults = [int(x) for x in _TEMPLATE[config_name].split(",")]
        return [k for k in defaults if k <= out_size]
    try:
        depths = validate_param(config_name, list(values))
    except (TypeError, ValueError) as e:
        raise UDLFParamError(str(e)) from None
    too_large = [k for k in depths if k > out_size]
    if too_large:
        raise UDLFParamError(f"{name} {too_large} are larger than the output ranked "
                             f"lists ({out_size} elements).")
    return depths


def _count_lines(path):
    with open(path, "rb") as f:
        return sum(1 for line in f if line.strip())


def _prepare_ranked_lists(value, dest):
    if isinstance(value, (str, os.PathLike)):
        path = os.path.abspath(os.path.expanduser(os.fspath(value)))
        _check_path(path)
        if not os.path.isfile(path):
            raise UDLFParamError(f"Ranked lists file not found: {path}")
        with open(path) as f:
            first = f.readline().split()
        if not first:
            raise UDLFParamError(f"Ranked lists file is empty: {path}")
        rk_format = "NUM" if all(x.isdigit() for x in first) else "STR"
        return _Source(path, _count_lines(path), "RK", rk_format)

    array = np.asarray(value)
    if array.ndim != 2 or array.size == 0:
        raise UDLFParamError(f"ranked_lists must be a 2D array (queries x positions), "
                             f"got shape {array.shape}.")
    if not np.issubdtype(array.dtype, np.integer):
        raise UDLFParamError("ranked_lists must contain integer indices of elements "
                             f"(got {array.dtype}). For distances use matrix=.")
    n = array.shape[0]
    if array.min() < 0 or array.max() >= n:
        raise UDLFParamError(f"ranked_lists values must be indices in [0, {n - 1}].")
    np.savetxt(dest, array, fmt="%d")
    return _Source(str(dest), n, "RK", "NUM", array=array)


def _prepare_matrix(value, matrix_type, dest):
    matrix_type = _check_choice(matrix_type, ("dist", "sim"), "matrix_type")
    if isinstance(value, (str, os.PathLike)):
        path = os.path.abspath(os.path.expanduser(os.fspath(value)))
        _check_path(path)
        if not os.path.isfile(path):
            raise UDLFParamError(f"Matrix file not found: {path}")
        return _Source(path, _count_lines(path), "MATRIX", matrix_type=matrix_type)

    array = np.asarray(value, dtype=np.float64)
    if array.ndim != 2 or array.shape[0] != array.shape[1] or array.size == 0:
        raise UDLFParamError(f"matrix must be square (N x N), got shape {array.shape}.")
    np.savetxt(dest, array, fmt="%.9g")
    return _Source(str(dest), array.shape[0], "MATRIX", matrix_type=matrix_type,
                   array=array)


def _prepare_names(names, n, dest):
    """Path of the lists file UDLF needs, and the names as a list (or None)."""
    if names is None:
        names_list = [str(i) for i in range(n)]
    elif isinstance(names, (str, os.PathLike)):
        path = os.path.abspath(os.path.expanduser(os.fspath(names)))
        _check_path(path)
        if not os.path.isfile(path):
            raise UDLFParamError(f"Names (lists) file not found: {path}")
        names_list = Path(path).read_text().split()
        if len(names_list) != n:
            raise UDLFParamError(f"{path} has {len(names_list)} names, the input has {n} rows.")
        return path, names_list
    else:
        names_list = [str(x) for x in names]
    if len(names_list) != n:
        raise UDLFParamError(f"names has {len(names_list)} elements, the input has {n} rows.")
    bad = [x for x in names_list if not x or any(c.isspace() for c in x) or ":" in x]
    if bad:
        raise UDLFParamError(f"Names cannot be empty or contain spaces or ':' (UDLF "
                             f"file formats), e.g. {bad[0]!r}.")
    if len(set(names_list)) != n:
        raise UDLFParamError("Names must be unique.")
    dest.write_text("".join(f"{x}\n" for x in names_list))
    return str(dest), names_list


def _prepare_classes(classes, names, names_list, dest):
    """Path of the classes file UDLF needs, and the label of each element."""
    if classes is None:
        return None, None
    if isinstance(classes, (str, os.PathLike)):
        path = os.path.abspath(os.path.expanduser(os.fspath(classes)))
        _check_path(path)
        if not os.path.isfile(path):
            raise UDLFParamError(f"Classes file not found: {path}")
        if names is None:
            raise UDLFParamError("A classes file refers to element names: pass names= "
                                 "(the lists file, or the names in order).")
        try:
            labels = readData.classes_of(names_list, path)
        except KeyError as e:
            raise UDLFParamError(str(e)) from None
        return path, labels

    labels = list(classes)
    if len(labels) != len(names_list):
        raise UDLFParamError(f"classes has {len(labels)} labels, the input has "
                             f"{len(names_list)} rows.")
    text = [str(label) for label in labels]
    if any(not t or any(c.isspace() for c in t) for t in text):
        raise UDLFParamError("Class labels cannot be empty or contain spaces "
                             "(UDLF file format).")
    dest.write_text("".join(f"{name}:{label}\n" for name, label in zip(names_list, text)))
    return str(dest), labels


def _read_top(path, depth):
    """First `depth` tokens of each non-empty line of a ranked lists file."""
    with open(path) as f:
        return [line.split()[:depth] for line in f if line.strip()]


def _read_matrix(path, n, dtype):
    """Read a space separated N-row file written by UDLF into a 2D array."""
    with open(path) as f:
        tokens = f.read().split()
    if dtype is str:
        return np.array(tokens, dtype=str).reshape(n, -1)
    return np.array(tokens, dtype=np.float64 if dtype is np.float64 else np.int64) \
        .astype(dtype).reshape(n, -1)


def _metrics(log, task):
    """Metrics of a parsed UDLF log as {"before": .., "after": .., "gain": ..}."""
    if task == "FUSION":
        after = {k: v for k, v in log.items() if k != "Time"}
        return {"after": after} if after else {}
    measures = {k: v for k, v in log.items() if isinstance(v, dict)}
    if not measures:
        return {}
    return {section: {name: values[key] for name, values in measures.items()}
            for section, key in (("before", "Before"), ("after", "After"),
                                 ("gain", "Gain"))}
