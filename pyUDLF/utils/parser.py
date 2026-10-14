"""
Parser module for configuration and log files.
Handles reading and validation of UDLF config and log outputs.
"""



def read_config_values(config_file: str) -> dict:
    """
    Read a UDLF config file exactly as the UDLF binary does: spaces and tabs
    are removed, everything after '#' is a comment, the name ends at the first
    '=' and, when a variable is declared twice, the last value wins.

    Args:
        config_file (str): Path to the configuration file.

    Returns:
        dict: {variable name: value as string}
    """
    values = {}
    with open(config_file, "r") as f:
        for line in f:
            line = line.replace(" ", "").replace("\t", "").rstrip("\r\n")
            line = line.split("#", 1)[0]
            if "=" in line:
                name, value = line.split("=", 1)
                values[name] = value
    return values


def parse_config(config_file: str) -> dict:
    """
    Parse a UDLF configuration file into a dictionary of parameters.

    Args:
        config_file (str): Path to the configuration file.

    Returns:
        dict: Parsed configuration parameters.
    """
    values = read_config_values(config_file)

    def get(name):
        # variables not declared take the UDLF default (config/general.conf)
        return values.get(name, _UDLF_DEFAULTS.get(name, ""))

    params = {
        "task": get("UDL_TASK"),
        "in_file_format": get("INPUT_FILE_FORMAT"),
        "in_rk_format": get("INPUT_RK_FORMAT"),
        "out_file": get("OUTPUT_FILE"),
        "out_file_format": get("OUTPUT_FILE_FORMAT"),
        "out_rk_format": get("OUTPUT_RK_FORMAT"),
        "before_path": get("INPUT_FILE"),
        "list_path": get("INPUT_FILE_LIST"),
        "classes_path": get("INPUT_FILE_CLASSES"),
        "after_path": "",
        "rk_path": "",
        "matrix_path": "",
        "log_path": get("OUTPUT_LOG_FILE_PATH"),
        "images_path": get("INPUT_IMAGES_PATH"),
    }

    # Output file names written by UDLF (Udl::writeOutput)
    if params["out_file"] == "TRUE":
        base = get("OUTPUT_FILE_PATH")
        if params["out_file_format"] == "MATRIX":
            params["matrix_path"] = f"{base}.txt"
        elif params["out_rk_format"] in ("NUM", "STR"):
            params["rk_path"] = f"{base}.txt"
        elif params["out_rk_format"] == "ALL":
            params["rk_path"] = f"{base}_num.txt"  # also <base>_str.txt and html
        params["after_path"] = params["rk_path"] or params["matrix_path"]

    return params


# Defaults UDLF uses for variables that are not declared (config/general.conf)
_UDLF_DEFAULTS = {
    "UDL_TASK": "UDL",
    "INPUT_FILE_FORMAT": "AUTO",
    "INPUT_RK_FORMAT": "NUM",
    "INPUT_FILE": "input.txt",
    "INPUT_FILE_LIST": "list.txt",
    "INPUT_FILE_CLASSES": "classes.txt",
    "INPUT_IMAGES_PATH": "images/",
    "OUTPUT_FILE": "TRUE",
    "OUTPUT_FILE_FORMAT": "RK",
    "OUTPUT_RK_FORMAT": "NUM",
    "OUTPUT_FILE_PATH": "output",
    "OUTPUT_LOG_FILE_PATH": "log.txt",
}
