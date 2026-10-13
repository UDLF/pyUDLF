import os
import re
import requests
import tarfile
import tempfile
from pathlib import Path
import subprocess
from pyUDLF.utils import readData, outputType, evaluation, parser
import sys
import zipfile
from pyUDLF.utils.logger import get_logger


# ---------- Logger configuration ----------
# logger = logging.getLogger(__name__)
# if not logger.hasHandlers(): 
#     handler = logging.StreamHandler()
#     formatter = logging.Formatter("[%(levelname)s] %(message)s")
#     handler.setFormatter(formatter)
#     logger.addHandler(handler)
#     logger.setLevel(logging.INFO)
logger = get_logger(__name__)

# ---------- Paths ----------
user_home = Path.home()
pyudlf_dir = user_home / ".pyudlf"
udlf_install_path = pyudlf_dir / "bin"

bin_path = str(udlf_install_path / "udlf")
# Template of new InputType objects: the reference config.ini of UDLF v1.70,
# shipped with pyUDLF, so the defaults do not depend on a downloaded file.
bundled_config_path = str(Path(__file__).resolve().parent / "data" / "config.ini")
config_path = bundled_config_path

original_bin_path = bin_path
original_config_path = config_path
compressed_binary_path = str(pyudlf_dir / "udlf_bin.tar.gz")

# ---------- Detect OS ----------
if sys.platform.startswith("linux"):
    operating_system = "linux"
elif sys.platform.startswith("win"):
    operating_system = "windows"
else:
    operating_system = "unsupported"
    logger.warning("Unsupported operating system detected: %s", sys.platform)
    
# ---------- Binary URLs ----------
udlf_urls = {"linux": "http://udlf_linux.lucasvalem.com",
             "windows": "http://udlf_windows.lucasvalem.com"}

#---------
def setBinaryPath(path: str) -> None:
    """
    Set the path of the UDLF binary used by run() and runWithConfig().

    Raises:
        FileNotFoundError: if there is no file at the given path.
    """
    global bin_path
    path = os.path.expanduser(str(path))
    if not os.path.isfile(path):
        raise FileNotFoundError(f"UDLF binary not found at: {path}")
    bin_path = path
    logger.info(f"Binary path set to: {bin_path}")


def getBinaryPath() -> str:
    """
    Return the current binary path.
    """
    global bin_path
    # logger.info(f"Current binary path: {bin_path}")
    return bin_path


def setConfigPath(path: str) -> None:
    """
    Set the path of the template config used by new InputType objects.

    Raises:
        FileNotFoundError: if there is no file at the given path.
    """
    global config_path
    path = os.path.expanduser(str(path))
    if not os.path.isfile(path):
        raise FileNotFoundError(f"UDLF config not found at: {path}")
    config_path = path
    logger.info(f"Config path set to: {config_path}")


def getConfigPath() -> str:
    """
    Return the current config path.
    """
    global config_path
    # logger.info(f"Current config path: {config_path}")
    return config_path


def download_url(url: str, save_path: str, chunk_size: int = 128) -> bool:
    """
    Download a file from a given URL and save it locally.

    Args:
        url (str): URL to download the file from.
        save_path (str): Path to save the downloaded file.
        chunk_size (int): Size of chunks to stream the download. Default is 128.

    Returns:
        bool: True if download succeeded, False otherwise.
    """
    logger.info(f"Starting download from {url}")
    try:
        response = requests.get(url, stream=True, timeout=30)
        response.raise_for_status()

        save_path = Path(save_path)
        save_path.parent.mkdir(parents=True, exist_ok=True)

        total_size = int(response.headers.get("content-length", 0))
        downloaded = 0

        with open(save_path, "wb") as fd:
            for chunk in response.iter_content(chunk_size=chunk_size):
                if chunk:
                    fd.write(chunk)
                    downloaded += len(chunk)
                    if total_size > 0:
                        percent = (downloaded / total_size) * 100
                        logger.debug(f"Downloaded {percent:.2f}%")

        logger.info(f"Download complete. File saved at: {save_path}")
        return True

    except requests.exceptions.RequestException as e:
        logger.error(f"Failed to download UDLF binary from {url}: {e}")
        return False
    except Exception as e:
        logger.error(f"Unexpected error while saving binary: {e}")
        return False


def verify_bin(config_path: str, bin_path: str) -> None:
    """
    Verify if UDLF binary and config exist. If not, download and extract them.

    Args:
        config_path (str): Path to the config file.
        bin_path (str): Path to the UDLF binary.
    """
    global operating_system
    global compressed_binary_path

    # Check if binary and config already exist
    if os.path.isfile(bin_path) and os.path.isfile(config_path):
        logger.info("UDLF binary and config found successfully.")
        return

    logger.warning("UDLF binary or config is missing...")

    # Ensure ~/.pyudlf directory exists
    logger.debug(f"Ensuring installation directory exists at {pyudlf_dir}")
    try:
        os.makedirs(pyudlf_dir, exist_ok=True)
    except Exception as e:
        logger.error(f"Could not create directory {pyudlf_dir}: {e}")
        return

    # Get download URL for the current OS
    url = udlf_urls.get(operating_system)
    if not url:
        logger.error(f"No download URL available for OS: {operating_system}")
        return

    # Download the binary archive
    logger.info(f"Attempting to download UDLF binary from {url}")
    logger.debug(f"File will be saved to {compressed_binary_path}")
    try:
        download_success = download_url(url, compressed_binary_path)
    except Exception as e:
        logger.error(f"Could not download file due to exception: {e}")
        return

    if not download_success:
        logger.error(f"Could not download file! Invalid URL {url}")
        return

    # Extract the binary according to the operating system
    try:
        if operating_system == "linux":
            with tarfile.open(compressed_binary_path, "r:gz") as archive:
                archive.extractall(pyudlf_dir)
            logger.info(f"UDLF binary extracted to {pyudlf_dir} (tar.gz)")

        elif operating_system == "windows":
            with zipfile.ZipFile(compressed_binary_path, "r") as archive:
                archive.extractall(pyudlf_dir)
            logger.info(f"UDLF binary extracted to {pyudlf_dir} (zip)")

        else:
            logger.error(f"Unsupported operating system: {operating_system}")
            return

    except Exception as e:
        logger.error(f"Failed to extract binary from {compressed_binary_path}: {e}")
        return
    logger.debug(f"Extraction complete, checking for binary at {bin_path}")


def run_platform(config_file: str, bin_path: str):
    """
    Run the UDLF binary with the given config file and verify execution.

    Args:
        config_file (str): Path to the configuration file.
        bin_path (str): Path to the UDLF binary.

    Returns:
        tuple:
            bool: True if the run FAILED, False if it completed correctly.
            str: Everything UDLF printed (stdout and stderr).
    """
    # Ensure binary and config exist (download/extract if missing)
    verify_bin(config_file, bin_path)

    logger.info(f"Running UDLF framework with config: {config_file}")
    output, problems = execute_udlf(config_file, bin_path)
    if problems:
        for problem in problems:
            logger.error(problem)
        if output:
            logger.error("Last lines printed by UDLF:\n%s", _tail(output))
        return True, output

    logger.info("UDLF run successfully.")
    return False, output


def execute_udlf(config_file: str, bin_path: str, cwd: str = None):
    """
    Run the UDLF binary on a config file and diagnose the run.

    Args:
        config_file (str): Path to the configuration file.
        bin_path (str): Path to the UDLF binary.
        cwd (str, optional): Working directory of the process (relative
            paths in the config are relative to it). Default: current one.

    Returns:
        tuple:
            str: Everything UDLF printed (stdout and stderr).
            list[str]: Problems found (see verify_running); empty if the run is OK.
    """
    cmd = [bin_path, config_file]
    if operating_system == "windows":
        cmd = ["cmd", "/c"] + cmd
    logger.debug(f"Command: {' '.join(cmd)}")

    try:
        proc = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                              text=True, errors="replace", check=False, cwd=cwd)
    except OSError as e:
        return "", [f"Failed to run UDLF binary {bin_path}: {e}"]

    return proc.stdout, verify_running(proc.returncode, proc.stdout)


# Messages UDLF prints when it replaces a value set by the user with its
# default. The run still exits with code 0, so they are checked explicitly.
_REJECTED_VALUE_PATTERNS = [
    re.compile(r"\*WARNING: You've declared (\S+) = (.*?)! Expected values are: \[(.*?)\]"),
    re.compile(r"\*WARNING: Type of (\S+) is (\w+)! (.*?) is invalid!"),
]
_SIGNAL_HINTS = {
    11: "segmentation fault; this usually means the input ranked lists are shorter "
        "than the method's L parameter, or SIZE_DATASET does not match the input",
}


def verify_running(returncode: int, output: str) -> list:
    """
    Decide whether a UDLF run failed.

    UDLF exits with code 1 on every validation or input error, and a crash
    shows up as a negative return code (killed by a signal). Some invalid
    values are only replaced by their defaults with a warning, so those
    messages are reported too.

    Args:
        returncode (int): return code of the UDLF process.
        output (str): everything UDLF printed.

    Returns:
        list[str]: description of each problem found; empty if the run is OK.
    """
    problems = []
    if returncode < 0:
        signal = -returncode
        hint = _SIGNAL_HINTS.get(signal, "")
        problems.append(f"UDLF was killed by signal {signal}" + (f" ({hint})" if hint else ""))
    elif returncode != 0:
        problems.append(f"UDLF exited with code {returncode}")

    for pattern in _REJECTED_VALUE_PATTERNS:
        for match in pattern.finditer(output):
            problems.append(
                f"UDLF rejected {match.group(1)} = {match.group(2).strip()!r} "
                "and used its default value instead")

    for line in output.splitlines():
        if line.strip().endswith("is being declared again!"):
            logger.warning(f"UDLF: {line.strip()} (the last value is used)")

    return problems


def _tail(text: str, lines: int = 15) -> str:
    return "\n".join(text.rstrip().splitlines()[-lines:])

def individual_gain_config_running(config_file: str, depth: int = -1):
    """
    Compute individual gain using parameters defined in a UDLF config file.

    Args:
        config_file (str): Path to configuration file.
        depth (int, optional): Depth to compute gain. If -1, uses dataset size.

    Returns:
        list or None: List of individual gains if computation is possible,
                      None otherwise.
    """
    try:
        params = parser.parse_config(config_file)
    except Exception as e:
        logger.error(f"Failed to parse config file {config_file}: {e}")
        return None

    # --- Validations ---
    if params["task"] != "UDL":
        logger.error("Task must be UDL. Running without calculating individual gain!")
        return None

    if params["out_file"] != "TRUE":
        logger.error("OUTPUT_FILE must be TRUE to calculate individual gain.")
        return None

    if params["in_file_format"] == "MATRIX":
        logger.error("Input file must be ranked list type, not MATRIX.")
        return None

    if params["in_file_format"] == "AUTO":
        logger.error("Input format set to AUTO. Expected ranked list type.")
        return None

    if params["in_rk_format"] != "NUM" or params["out_rk_format"] != "NUM":
        logger.error("Input and output must be numerical (NUM) format.")
        return None

    if params["out_file_format"] != "RK":
        logger.error("Output file must be ranked list type (RK).")
        return None

    # --- Read data ---
    try:
        classes_list = readData.read_classes(params["list_path"], params["classes_path"])
        rks_after = readData.read_ranked_lists_file_numeric(params["after_path"])
        # UDLF outputs lists of size L; by default the gain uses the whole
        # output lists, i.e. the same depth as the MAP in the UDLF log
        if depth == -1:
            depth = min(len(rk) for rk in rks_after)
        rks_before = readData.read_ranked_lists_file_numeric(params["before_path"], top_k=depth)
    except Exception as e:
        logger.error(f"Failed to read input/output ranked lists: {e}")
        return None

    # --- Compute gain ---
    try:
        individual_gain_list = evaluation.compute_gain(
            rks_before, rks_after, classes_list, depth, measure="MAP", verbose=True)
        logger.info("Individual gain computation completed successfully.")
        #print(individual_gain_list)
        return individual_gain_list
    except Exception as e:
        logger.error(f"Error computing individual gain: {e}")
        return None


def validate_config_and_binary(config_file: str, bin_path: str) -> bool:
    """
    Validate that config file and binary exist. If the binary is missing,
    attempt to download and install it.

    Args:
        config_file (str): Path to the configuration file.
        bin_path (str): Path to the UDLF binary.

    Returns:
        bool: True if validation passes, False otherwise.
    """
    if not os.path.isfile(config_file):
        logger.error("Config file is missing! Unable to run.")
        return False

    if not os.path.isfile(bin_path):
        logger.warning("Binary is missing! Attempting to download...")
        verify_bin(config_file, bin_path)

    return True

def prepare_visualization(params: dict, output: "OutputType") -> bool:
    """
    Prepare visualization data for RK/NUM outputs.
    Updates the output object in place.

    Args:
        params (dict): Parsed config parameters.
        output (OutputType): Output object to update.

    Returns:
        bool: True if visualization paths were set successfully, False otherwise.
    """
    out_format = params.get("out_file_format", "")
    out_rk_format = params.get("out_rk_format", "")
    img_path = params.get("images_path", "")
    list_path = params.get("list_path", "")
    classes_path = params.get("classes_path","")

    if out_format != "RK":
        logger.error("The output file must be of type 'RK'.")
        return False
    if out_rk_format not in ("NUM", "ALL"):
        logger.error("The output format of the ranked lists must be 'NUM' or 'ALL'.")
        return False
    if not os.path.isdir(img_path):
        logger.warning(f"Images directory does not exist: {img_path}")
        return False

    if not os.path.isfile(list_path):
        logger.warning(f"List file does not exist: {list_path}")
        return False

    if not os.path.isfile(classes_path):
        logger.warning(f"Classes file does not exist: {classes_path}")
        return False

    # If everything is valid, update output
    output.images_path = img_path
    output.list_path = params.get("list_path", "")
    output.classes_path = params.get("classes_path","")
    logger.info("Visualization paths set successfully.")
    return True

def _required_columns(values: dict):
    """
    Number of elements UDLF reads from each line of a ranked lists input,
    or None when it cannot be determined from the config.
    """
    method = values.get("UDL_METHOD", "")
    try:
        n = int(values["SIZE_DATASET"])
        if method in ("CONTEXTRR", "RLSIM"):  # these read the full ranked lists
            return n
        if method == "RDPAC":
            l = int(values["PARAM_RDPAC_L"])
            l_mult = float(values["PARAM_RDPAC_L_MULT"])
            if l_mult * l > n:  # RDPAC.cpp reduces L itself in this case
                l = int(n / l_mult)
            return int(l_mult * l)
        return int(values[f"PARAM_{method}_L"])
    except (KeyError, ValueError):
        return None


def check_input_files(config_file: str) -> list:
    """
    Check the ranked lists inputs of a config before running UDLF.

    UDLF reads exactly SIZE_DATASET lines with L elements each. If a line is
    shorter, it silently continues reading from the next line and, at the end
    of the file, repeats the last value: the run "succeeds" with wrong results
    (or crashes, depending on the sizes). This check turns that into an error.

    Args:
        config_file (str): Path to the configuration file.

    Returns:
        list[str]: description of each problem found; empty if inputs are OK.
    """
    values = parser.read_config_values(config_file)
    if values.get("INPUT_FILE_FORMAT", "AUTO") not in ("RK", "AUTO"):
        return []
    try:
        n = int(values["SIZE_DATASET"])
    except (KeyError, ValueError):
        return []
    required = _required_columns(values)

    if values.get("UDL_TASK") == "FUSION":
        try:
            count = int(values.get("NUM_INPUT_FUSION_FILES", "0"))
        except ValueError:
            return []
        files = [values.get(f"INPUT_FILES_FUSION_{i}") for i in range(1, count + 1)]
    else:
        files = [values.get("INPUT_FILE")]

    problems = []
    for path in files:
        if not path or not os.path.isfile(path):
            problems.append(f"Input file not found: {path}")
            continue
        rows = 0
        short_line = None
        with open(path, "r", errors="replace") as f:
            for line in f:
                if rows == n:
                    break
                if required is not None and len(line.split(None, required)) < required:
                    short_line = (rows + 1, len(line.split()))
                    break
                rows += 1
        if short_line:
            problems.append(
                f"Line {short_line[0]} of {path} has {short_line[1]} elements, but "
                f"{values.get('UDL_METHOD')} reads {required} per line "
                "(the method's L parameter). Use ranked lists of size >= L, or reduce L.")
        elif rows < n:
            problems.append(f"{path} has {rows} lines, but SIZE_DATASET = {n}.")
    return problems


def runWithConfig(
    config_file: str = None,
    get_output: bool = False,
    compute_individual_gain: bool = False,
    depth: int = -1,
    visualization: bool = False
):
    """
    Run UDLF framework with an existing configuration file.
    """
    global bin_path
    output = outputType.OutputType()

    # Step 1: validate config and binary
    if not validate_config_and_binary(config_file, bin_path):
        return False
    input_problems = check_input_files(config_file)
    if input_problems:
        for problem in input_problems:
            logger.error(problem)
        logger.error("UDLF was not executed: invalid input.")
        return False

    # Step 2: run platform
    failed, udlf_output = run_platform(config_file, bin_path)
    if failed:
        logger.error("UDLF execution failed.")
        return False
    output.stdout = udlf_output
    logger.info("pyUDLF execution complete!")

    # Step 3: parse config + log if requested
    params = {}
    if get_output:
        try:
            params = parser.parse_config(config_file)
            output.rk_path = params["rk_path"]
            output.matrix_path = params["matrix_path"]
            output.log_path = params["log_path"]
            output.classes_path = params["classes_path"]
            output.list_path = params["list_path"]
            output.images_path = params["images_path"]
            output.log_dict = readData.parse_log(udlf_output)
        except Exception as e:
            logger.error(f"Error parsing config file {config_file}: {e}")
            return False

    # Step 4: compute individual gain if requested
    if compute_individual_gain:
        ig_list = individual_gain_config_running(config_file, depth)
        if ig_list is None:
            logger.warning("Individual gain could not be computed. Continuing without it.")
        else:
            output.individual_gain_list = ig_list

    # Step 5: visualization
    if visualization:
        if get_output:
            success = prepare_visualization(params, output)
            if not success:
                logger.error("Visualization requested but could not be prepared.")
        else:
            logger.error("Visualization requested but output parsing was not enabled.")

    return output

def run(
    input_type,
    get_output: bool = False,
    compute_individual_gain: bool = False,
    depth: int = -1,
    visualization: bool = False
):
    """
    Run UDLF with a generated configuration file.

    Args:
        input_type: InputType object, must contain a valid config_path.
        get_output (bool, optional): If True, parse and return output paths.
        compute_individual_gain (bool, optional): If True, compute individual gain list.
        depth (int, optional): Depth for gain computation. Default is -1.
        visualization (bool, optional): If True, prepare visualization info.

    Returns:
        OutputType or False: OutputType object with parsed results, or False if execution failed.
    """
    if not os.path.isfile(input_type.config_path):
        logger.error("Unable to run: input_type was not initialized correctly (missing config).")
        return False

    global bin_path

    # Create a unique temporary config file
    tmp_file = tempfile.NamedTemporaryFile(suffix=".ini", delete=False)
    input_path = tmp_file.name
    tmp_file.close()  # close so input_type can write into it

    try:
        # Write config and run
        input_type.write_config(input_path)
        logger.debug(f"Temporary config written: {input_path}")

        output = runWithConfig(
            config_file=input_path,
            get_output=get_output,
            compute_individual_gain=compute_individual_gain,
            depth=depth,
            visualization=visualization
        )

        return output

    except Exception as e:
        logger.error(f"Error during run execution: {e}")
        return False

    finally:
        # Always clean up temp config
        if os.path.exists(input_path):
            os.remove(input_path)
            logger.debug(f"Temporary config removed: {input_path}")

