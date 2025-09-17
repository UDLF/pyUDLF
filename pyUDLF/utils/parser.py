"""
Parser module for configuration and log files.
Handles reading and validation of UDLF config and log outputs.
"""

import os
import logging
from pyUDLF.utils import readData

# Module-level logger (public lib style: no handler here)
logger = logging.getLogger(__name__)

def parse_config(config_file: str) -> dict:
    """
    Parse a UDLF configuration file into a dictionary of parameters.

    Args:
        config_file (str): Path to the configuration file.

    Returns:
        dict: Parsed configuration parameters.
    """
    params = {
        "task": "",
        "in_file_format": "",
        "in_rk_format": "",
        "out_file": "",
        "out_file_format": "",
        "out_rk_format": "",
        "before_path": "",
        "list_path": "",
        "classes_path": "",
        "after_path": "",
        "rk_path": "",
        "matrix_path": "",
        "log_path": ""
    }
    with open(config_file, "r") as f:
        lines = [line.strip() for line in f if line.strip()]

    for line in lines:
        if line.startswith("UDL_TASK"):
            params["task"] = line.split("=")[1].split("#")[0].strip()

        elif line.startswith("INPUT_FILE "):  # explicit INPUT_FILE
            params["before_path"] = line.split("=")[1].split("#")[0].strip()

        elif line.startswith("INPUT_FILE_LIST"):
            params["list_path"] = line.split("=")[1].split("#")[0].strip()

        elif line.startswith("INPUT_FILE_CLASSES"):
            params["classes_path"] = line.split("=")[1].split("#")[0].strip()

        elif line.startswith("INPUT_FILE_FORMAT"):
            params["in_file_format"] = line.split("=")[1].split("#")[0].strip()

        elif line.startswith("INPUT_RK_FORMAT"):
            params["in_rk_format"] = line.split("=")[1].split("#")[0].strip()

        elif line.startswith("OUTPUT_FILE "):  # explicit OUTPUT_FILE
            params["out_file"] = line.split("=")[1].split("#")[0].strip()

        elif line.startswith("OUTPUT_FILE_FORMAT"):
            params["out_file_format"] = line.split("=")[1].split("#")[0].strip()

        elif line.startswith("OUTPUT_RK_FORMAT"):
            params["out_rk_format"] = line.split("=")[1].split("#")[0].strip()

        elif line.startswith("OUTPUT_FILE_PATH"):
            base = line.split("=")[1].split("#")[0].strip()
            if params["out_file_format"] == "RK":
                params["rk_path"] = f"{base}.txt"
            elif params["out_file_format"] == "MATRIX":
                params["matrix_path"] = f"{base}.txt"
            params["after_path"] = f"{base}.txt"  # useful for before/after comparison

        elif line.startswith("OUTPUT_LOG_FILE_PATH"):
            params["log_path"] = line.split("=")[1].split("#")[0].strip()

    return params
    
    
def parse_log_and_cleanup(log_out_path: str) -> dict:
    """
    Read execution log and remove temporary log file.

    Args:
        log_out_path (str): Path to the temporary log file.

    Returns:
        dict: Parsed log dictionary.
    """
    try:
        log_dict = readData.read_log(log_out_path)
        os.remove(log_out_path)
        logger.debug(f"Temporary log file removed: {log_out_path}")
        return log_dict
    except Exception as e:
        logger.error(f"Failed to read or remove log file {log_out_path}: {e}")
        return {}
