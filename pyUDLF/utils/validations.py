"""
Validation rules for UDLF config parameters.
Generated from config.ini specification.
"""

from pyUDLF.utils.logger import get_logger
from pathlib import Path

logger = get_logger(__name__)

VALIDATIONS = {
    # ========================
    # GENERAL CONFIGURATION
    # ========================
    "UDL_TASK": {"type": "enum", "values": {"UDL", "FUSION"}},
    "UDL_METHOD": {"type": "enum", "values": {
        "NONE", "CPRR", "RLRECOM", "RLSIM", "CONTEXTRR",
        "RECKNNGRAPH", "RKGRAPH", "CORGRAPH", "LHRR",
        "BFSTREE", "RDPAC", "RFE"
    }},

    # ========================
    # INPUT DATASET FILES
    # ========================
    "SIZE_DATASET": {"type": "uint"},
    "INPUT_FILE_FORMAT": {"type": "enum", "values": {"AUTO", "MATRIX", "RK"}},
    "INPUT_MATRIX_TYPE": {"type": "enum", "values": {"DIST", "SIM"}},
    "INPUT_RK_FORMAT": {"type": "enum", "values": {"NUM", "STR"}},
    "MATRIX_TO_RK_SORTING": {"type": "enum", "values": {"HEAP", "INSERTION"}},
    "NUM_INPUT_FUSION_FILES": {"type": "uint"},
    # Paths: INPUT_FILES_FUSION_*, INPUT_FILE, INPUT_FILE_LIST, INPUT_FILE_CLASSES, INPUT_IMAGES_PATH
    # These can be any string, so we won't restrict.

    # ========================
    # OUTPUT FILES SETTINGS
    # ========================
    "OUTPUT_FILE": {"type": "bool"},
    "OUTPUT_FILE_FORMAT": {"type": "enum", "values": {"RK", "MATRIX"}},
    "OUTPUT_MATRIX_TYPE": {"type": "enum", "values": {"DIST", "SIM"}},
    "OUTPUT_RK_FORMAT": {"type": "enum", "values": {"NUM", "STR", "HTML", "ALL"}},
    "OUTPUT_HTML_RK_PER_FILE": {"type": "uint"},
    "OUTPUT_HTML_RK_SIZE": {"type": "uint"},
    "OUTPUT_HTML_RK_COLORS": {"type": "bool"},
    "OUTPUT_HTML_RK_BEFORE_AFTER": {"type": "bool"},
    # Paths: OUTPUT_FILE_PATH, OUTPUT_LOG_FILE_PATH → free strings

    # ========================
    # EVALUATION SETTINGS
    # ========================
    "EFFICIENCY_EVAL": {"type": "bool"},
    "EFFECTIVENESS_EVAL": {"type": "bool"},
    "EFFECTIVENESS_COMPUTE_PRECISIONS": {"type": "bool"},
    "EFFECTIVENESS_COMPUTE_MAP": {"type": "bool"},
    "EFFECTIVENESS_COMPUTE_RECALL": {"type": "bool"},
    "EFFECTIVENESS_RECALLS_TO_COMPUTE": {"type": "list_uint"},
    "EFFECTIVENESS_PRECISIONS_TO_COMPUTE": {"type": "list_uint"},

    # ========================
    # METHOD PARAMETERS
    # ========================
    # NONE
    "PARAM_NONE_L": {"type": "uint"},

    # CONTEXTRR
    "PARAM_CONTEXTRR_L": {"type": "uint"},
    "PARAM_CONTEXTRR_K": {"type": "uint"},
    "PARAM_CONTEXTRR_T": {"type": "uint"},
    "PARAM_CONTEXTRR_NBYK": {"type": "uint"},
    "PARAM_CONTEXTRR_OPTIMIZATIONS": {"type": "bool"},

    # CORGRAPH
    "PARAM_CORGRAPH_L": {"type": "uint"},
    "PARAM_CORGRAPH_K": {"type": "uint"},
    "PARAM_CORGRAPH_THRESHOLD_START": {"type": "float", "min": 0, "max": 1},
    "PARAM_CORGRAPH_THRESHOLD_END": {"type": "float", "min": 0, "max": 1},
    "PARAM_CORGRAPH_THRESHOLD_INC": {"type": "float", "min": 0.0},
    "PARAM_CORGRAPH_CORRELATION": {"type": "enum", "values": {"PEARSON", "RBO"}},

    # CPRR
    "PARAM_CPRR_L": {"type": "uint"},
    "PARAM_CPRR_K": {"type": "uint"},
    "PARAM_CPRR_T": {"type": "uint"},

    # RKGRAPH
    "PARAM_RKGRAPH_K": {"type": "uint"},
    "PARAM_RKGRAPH_T": {"type": "uint"},
    "PARAM_RKGRAPH_P": {"type": "float", "min": 0, "max": 1},
    "PARAM_RKGRAPH_L": {"type": "uint"},

    # RECKNNGRAPH
    "PARAM_RECKNNGRAPH_L": {"type": "uint"},
    "PARAM_RECKNNGRAPH_K": {"type": "uint"},
    "PARAM_RECKNNGRAPH_EPSILON": {"type": "float", "min": 0},

    # RLRECOM
    "PARAM_RLRECOM_L": {"type": "uint"},
    "PARAM_RLRECOM_K": {"type": "uint"},
    "PARAM_RLRECOM_LAMBDA": {"type": "float", "min": 0},
    "PARAM_RLRECOM_EPSILON": {"type": "float", "min": 0},

    # RLSIM
    "PARAM_RLSIM_TOPK": {"type": "uint"},
    "PARAM_RLSIM_CK": {"type": "uint"},
    "PARAM_RLSIM_T": {"type": "uint"},
    "PARAM_RLSIM_METRIC": {"type": "enum", "values": {
        "INTERSECTION", "RBO", "KENDALL_TAU", "SPEARMAN",
        "GOODMAN", "JACCARD", "JACCARD_K", "KENDALL_TAU_W"
    }},

    # LHRR
    "PARAM_LHRR_K": {"type": "uint"},
    "PARAM_LHRR_L": {"type": "uint"},
    "PARAM_LHRR_T": {"type": "uint"},

    # BFSTREE
    "PARAM_BFSTREE_L": {"type": "uint"},
    "PARAM_BFSTREE_K": {"type": "uint"},
    "PARAM_BFSTREE_CORRELATION_METRIC": {"type": "enum", "values": {"RBO"}},

    # RDPAC
    "PARAM_RDPAC_K_END": {"type": "uint"},
    "PARAM_RDPAC_K_INC": {"type": "uint"},
    "PARAM_RDPAC_K_START": {"type": "uint"},
    "PARAM_RDPAC_L": {"type": "uint"},
    "PARAM_RDPAC_L_MULT": {"type": "uint"},
    "PARAM_RDPAC_P": {"type": "float", "min": 0, "max": 1},
    "PARAM_RDPAC_PL": {"type": "float", "min": 0, "max": 1},

    # RFE
    "PARAM_RFE_K": {"type": "uint"},
    "PARAM_RFE_T": {"type": "uint"},
    "PARAM_RFE_L": {"type": "uint"},
    "PARAM_RFE_PA": {"type": "float", "min": 0, "max": 1},
    "PARAM_RFE_TH_CC": {"type": "uint"},
    "PARAM_RFE_RERANK_BY_EMB": {"type": "bool"},
    "PARAM_RFE_EXPORT_EMBEDDINGS": {"type": "bool"},
    "PARAM_RFE_PERFORM_CCS": {"type": "bool"},
    # Paths: PARAM_RFE_EMBEDDINGS_PATH, PARAM_RFE_CCS_PATH → free strings
}

def validate_param(key: str, value):
    """
    Validate a parameter based on VALIDATIONS rules.
    Returns the normalized value if valid.
    Raises ValueError if invalid.
    """
    rules = VALIDATIONS.get(key)
    if not rules:
        return value  # no validation rules

    t = rules["type"]

    # ENUM
    if t == "enum":
        if isinstance(value, str):
            val = value.upper()
            #print(f"DEBUG validate_param: key={key}, raw={value}, normalized={val}, allowed={rules['values']}")
            if val in rules["values"]:
                return val
        raise ValueError(f"Invalid value '{value}' for {key}. Allowed: {rules['values']}")

    # BOOL
    if t == "bool":
        if isinstance(value, str):
            val = value.upper()
            if val in {"TRUE", "FALSE"}:
                return val
        if isinstance(value, bool):
            return "TRUE" if value else "FALSE"
        raise ValueError(f"Invalid value '{value}' for {key}. Must be TRUE/FALSE.")

    # UINT
    if t == "uint":
        if isinstance(value, int) and value >= 0:
            return value
        raise ValueError(f"Invalid value '{value}' for {key}. Must be unsigned integer.")

    # FLOAT
    if t == "float":
        try:
            f = float(value)
        except Exception:
            raise ValueError(f"Invalid value '{value}' for {key}. Must be float.")
        if "min" in rules and f < rules["min"]:
            raise ValueError(f"{key} must be >= {rules['min']}")
        if "max" in rules and f > rules["max"]:
            raise ValueError(f"{key} must be <= {rules['max']}")
        return f

    # LIST_UINT
    if t == "list_uint":
        if isinstance(value, str):
            items = [int(x) for x in value.split(",")]
            if all(x >= 0 for x in items):
                return items
        if isinstance(value, (list, tuple)):
            if all(isinstance(x, int) and x >= 0 for x in value):
                return list(value)
        raise ValueError(f"Invalid value '{value}' for {key}. Must be list of unsigned integers.")

    return value

from pathlib import Path

def validate_path(value: str, must_exist: bool = False) -> str:
    """
    Validate a file or directory path.

    Args:
        value (str): the path to validate.
        must_exist (bool): if True, check that the path exists.

    Returns:
        str: the validated path.

    Raises:
        ValueError: if path is invalid, contains spaces/special characters,
                    or does not exist when must_exist=True.
    """
    if not isinstance(value, str) or not value.strip():
        raise ValueError("Path must be a non-empty string.")

    # Normalize
    path_str = value.strip()
    path = Path(path_str)

    # Basic forbidden characters (expand if needed)
    forbidden = [' ', '(', ')', '[', ']', '{', '}', ';', '"', "'"]
    if any(ch in path_str for ch in forbidden):
        raise ValueError(
            f"Invalid path '{path_str}'. It contains spaces or forbidden characters."
        )

    # Optional existence check
    if must_exist and not path.exists():
        raise ValueError(f"Path does not exist: {path_str}")

    return path_str