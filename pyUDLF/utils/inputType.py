import os
from pyUDLF.utils import configGenerator
from pyUDLF import run_calls
from pyUDLF.utils.logger import get_logger
from pyUDLF.utils.validations import validate_param, validate_path, METHOD_PARAMS
from pyUDLF.utils.visualization import render_ranked_list
from pathlib import Path
logger = get_logger(__name__)

class InputType:
    """
    Handle the input configuration for UDLF executions.

    This class manages input files, parameters, and config paths. It can be
    initialized with an existing config file or with input files directly,
    automatically preparing the configuration for UDLF.
    """

    def __init__(self, config_path=None, input_files=None):
        """
        Initialize the InputType instance.

        Args:
            config_path (str, optional): Path to the UDLF config file. If None,
                                         the default from run_calls is used.
            input_files (str | list | list[list], optional): Input files to
                                         initialize immediately.
                                         - str: single file path
                                         - list[str]: multiple file paths (fusion mode)
                                         - list[list]: ranked lists, which will be
                                                       written to disk before use
        """
        self.parameters = dict()
        self.list_parameters = []
        self.input_files_list = input_files
        self.config_path = config_path
        # If no config path is provided, use default from run_calls
        # and ensure the binary/config are available
        if self.config_path is None:
            self.config_path = run_calls.config_path
            if not os.path.isfile(self.config_path):
                logger.warning("Config is missing! Will try to install/verify UDLF assets.")
                run_calls.verify_bin(self.config_path, run_calls.bin_path)
            logger.info("InputType initialized.")

        # Load parameters from config; abort initialization if it fails
        ok = self.init_parameters(self.config_path)  # now returns bool
        if not ok:
            logger.error("Failed to initialize parameters from config. Instance will be empty.")
            return

        # If input_files were provided, initialize them immediately
        if input_files is not None:
            self.init_data()

    def init_parameters(self, path):
        """
        Load parameters from a config file.

        Args:
            path (str): Path to the config file.

        Returns:
            bool: True if parameters were loaded successfully,
                  False if loading failed.
        """
        self.parameters, self.list_parameters = configGenerator.initParameters(
            path, self.parameters, self.list_parameters)

        if not self.parameters:  # explicit check
            logger.error("Could not load parameters from config '%s'.", path)
            return False

        return True
    
    def init_data(self):
        """
        Initialize input data depending on the type of `input_files_list`.

        Cases:
            - str: single file path.
            - list[str]: list of file paths (fusion mode).
            - list[list]: ranked lists, written to disk before being set.

        Raises:
            ValueError: if the input_files_list type is not supported.
        """
        if not self.input_files_list:
            logger.warning("Input files list is empty. Nothing to initialize.")
            return

        # Case 1: single path
        if isinstance(self.input_files_list, str):
            logger.debug("Initializing data with a single path.")
            self.set_input_files(self.input_files_list)
            return

        # Case 2: list input
        if isinstance(self.input_files_list, list):
            first_elem = self.input_files_list[0]

            # Case 2a: list of paths
            if isinstance(first_elem, str):
                logger.debug("Initializing data with a list of paths.")
                self.set_input_files(self.input_files_list)
                return

            # Case 2b: list of lists
            if isinstance(first_elem, list):
                logger.debug("Initializing data with a list of ranked lists (will be written to disk).")
                aux = os.path.dirname(self.config_path)
                data_paths = configGenerator.write_input_files(
                    self.input_files_list, aux
                )
                self.set_input_files(data_paths)
                return

        # Case not recognized
        logger.error("Unsupported type for input_files_list: %s", type(self.input_files_list))

    def _set_validated(self, key: str, value):
        """
        Validate and set a configuration parameter.

        The parameter name (`key`) is validated against the known config schema,
        and the value is normalized using `validate_param`. If the value is invalid,
        a ValueError is raised.

        Args:
            key (str): configuration parameter name.
            value: value to set for the parameter.

        Raises:
            ValueError: if the value is not valid for the given parameter.
        """
        normalized = validate_param(key, value)
        
            # --- FIX para listas virarem CSV no .ini ---
        if key in {"EFFECTIVENESS_RECALLS_TO_COMPUTE", "EFFECTIVENESS_PRECISIONS_TO_COMPUTE"}:
            # Aceita tanto lista quanto string e normaliza para "1,2,5,10,15"
            if isinstance(normalized, (list, tuple, set)):
                try:
                    normalized = ",".join(str(int(v)) for v in normalized)
                except Exception:
                    raise ValueError(
                        f"{key} must be a list of positive integers or a CSV string."
                    )
            elif isinstance(normalized, str):
                parts = [p.strip() for p in normalized.replace(" ", "").split(",") if p.strip()]
                if not parts or not all(p.isdigit() and int(p) > 0 for p in parts):
                    raise ValueError(f"{key} must be a CSV of positive integers, got: {normalized!r}")
                normalized = ",".join(parts)
            else:
                raise ValueError(f"{key} must be a list[int] or CSV string, got {type(normalized)}")

        configGenerator.setParameter(key, normalized, self.parameters)
        logger.debug("%s set to %r", key, normalized)

    def set_method_name(self, value: str) -> None:
        """
        Define the UDL method to be used.

        Args:
            value (str): method name.
                         Examples: 'NONE', 'CPRR', 'RFE'.
        """
        self._set_validated("UDL_METHOD", value)

    def set_task(self, value: str) -> None:
        """
        Define the UDL task type.

        Args:
            value (str): task type.
                         Must be either 'UDL' (single input)
                         or 'FUSION' (multiple inputs).
        """
        self._set_validated("UDL_TASK", value)

    def set_input_file_format(self, value: str) -> None:
        """
        Define the input file format.

        Args:
            value (str): format of the input file.
                         Must be one of: 'AUTO', 'MATRIX', 'RK'.

        Raises:
            ValueError: if the value is not a valid format.
        """
        self._set_validated("INPUT_FILE_FORMAT", value)

    def set_input_file(self, value: str) -> None:
        """
        Define the path to the main input file (matrix or ranked lists).

        Args:
            value (str): path to the input file.

        Raises:
            ValueError: if value is not a non-empty string.
        """
        # if not isinstance(value, str) or not value.strip():
        #     raise ValueError("Invalid input file path. Must be a non-empty string.")
        path_str = validate_path(value, must_exist=True)
        self._set_validated("INPUT_FILE", path_str)

    def set_output_file(self, value: bool) -> None:
        """
        Enable or disable generation of output files.

        Args:
            value (bool): True to generate output files, False otherwise.

        Raises:
            ValueError: if value is not boolean.
        """
        if not isinstance(value, bool):
            raise ValueError("Invalid output_file value. Must be True or False.")
        # no validate_param domain? convertemos para string "TRUE"/"FALSE"
        self._set_validated("OUTPUT_FILE", "TRUE" if value else "FALSE")

    def set_output_file_format(self, value: str) -> None:
        """
        Define the output file format.

        Args:
            value (str): output format.
                         Must be either 'RK' (ranked list) or 'MATRIX'.
        """
        self._set_validated("OUTPUT_FILE_FORMAT", value)

    def set_output_matrix_type(self, value: str) -> None:
        """
        Define the type of the output matrix.

        Args:
            value (str): matrix type.
                         Must be either 'DIST' (distance) or 'SIM' (similarity).
        """
        self._set_validated("OUTPUT_MATRIX_TYPE", value)

    def set_output_rk_format(self, value: str) -> None:
        """
        Define the output ranked list format.

        Args:
            value (str): ranked list format.
                         Must be one of: 'NUM' (numeric), 'STR' (string),
                         'HTML' (HTML format), or 'ALL' (all formats).
        """
        self._set_validated("OUTPUT_RK_FORMAT", value)


    def set_output_file_path(self, value: str) -> None:
        """
        Set the path of the output file.

        Args:
            value (str): path to the output (base name, without extension).
        """
        # if not isinstance(value, str) or not value.strip():
        #     raise ValueError("Invalid output file path. Must be a non-empty string.")
        # configGenerator.setParameter("OUTPUT_FILE_PATH", value, self.parameters)
        # logger.debug("OUTPUT_FILE_PATH set to %r", value)
        path_str = validate_path(value, must_exist=False)
        self._set_validated("OUTPUT_FILE_PATH", path_str)


    def set_output_html_rk_per_file(self, value: int) -> None:
        """
        Define the number of ranked lists per generated HTML file.

        Args:
            value (int): positive integer number of ranked lists per file.

        Raises:
            ValueError: if value is not a positive integer.
        """
        if not isinstance(value, int) or value <= 0:
            raise ValueError("Invalid OUTPUT_HTML_RK_PER_FILE. Must be a positive integer.")
        self._set_validated("OUTPUT_HTML_RK_PER_FILE", value)

    def set_output_html_rk_size(self, value: int) -> None:
        """
        Define the number of images per ranked list in the generated HTML.

        Args:
            value (int): positive integer, number of images per ranked list.

        Raises:
            ValueError: if value is not a positive integer.
        """
        if not isinstance(value, int) or value <= 0:
            raise ValueError("Invalid OUTPUT_HTML_RK_SIZE. Must be a positive integer.")
        self._set_validated("OUTPUT_HTML_RK_SIZE", value)

    def set_output_html_rk_colors(self, value: bool) -> None:
        """
        Enable or disable colored highlighting in HTML ranked lists.

        Args:
            value (bool): True to use colors, False otherwise.

        Raises:
            ValueError: if value is not boolean.
        """
        if not isinstance(value, bool):
            raise ValueError("Invalid OUTPUT_HTML_RK_COLORS. Must be True or False.")
        self._set_validated("OUTPUT_HTML_RK_COLORS", "TRUE" if value else "FALSE")

    def set_output_html_rk_before_after(self, value: bool) -> None:
        """
        Enable or disable showing ranked lists before and after execution in HTML output.

        Args:
            value (bool): True to show before/after, False otherwise.

        Raises:
            ValueError: if value is not boolean.
        """
        if not isinstance(value, bool):
            raise ValueError("Invalid OUTPUT_HTML_RK_BEFORE_AFTER. Must be True or False.")
        self._set_validated("OUTPUT_HTML_RK_BEFORE_AFTER", "TRUE" if value else "FALSE")

    def set_efficiency_eval(self, value: bool) -> None:
        """
        Enable or disable efficiency evaluation.

        Args:
            value (bool): True to enable, False to disable.

        Raises:
            ValueError: if value is not boolean.
        """
        if not isinstance(value, bool):
            raise ValueError("Invalid EFFICIENCY_EVAL. Must be True or False.")
        self._set_validated("EFFICIENCY_EVAL", "TRUE" if value else "FALSE")

    def set_effectiveness_eval(self, value: bool) -> None:
        """
        Enable or disable effectiveness evaluation.

        Args:
            value (bool): True to enable, False to disable.

        Raises:
            ValueError: if value is not boolean.
        """
        if not isinstance(value, bool):
            raise ValueError("Invalid EFFECTIVENESS_EVAL. Must be True or False.")
        self._set_validated("EFFECTIVENESS_EVAL", "TRUE" if value else "FALSE")

    def set_effectiveness_compute_precisions(self, value: bool) -> None:
        """
        Enable or disable computation of precision values.

        Args:
            value (bool): True to enable, False to disable.

        Raises:
            ValueError: if value is not boolean.
        """
        if not isinstance(value, bool):
            raise ValueError("Invalid EFFECTIVENESS_COMPUTE_PRECISIONS. Must be True or False.")
        self._set_validated("EFFECTIVENESS_COMPUTE_PRECISIONS", "TRUE" if value else "FALSE")

    def set_effectiveness_compute_map(self, value: bool) -> None:
        """
        Enable or disable computation of MAP (Mean Average Precision).

        Args:
            value (bool): True to enable, False to disable.

        Raises:
            ValueError: if value is not boolean.
        """
        if not isinstance(value, bool):
            raise ValueError("Invalid EFFECTIVENESS_COMPUTE_MAP. Must be True or False.")
        self._set_validated("EFFECTIVENESS_COMPUTE_MAP", "TRUE" if value else "FALSE")

    def set_effectiveness_compute_recall(self, value: bool) -> None:
        """
        Enable or disable computation of Recall values.

        Args:
            value (bool): True to enable, False to disable.

        Raises:
            ValueError: if value is not boolean.
        """
        if not isinstance(value, bool):
            raise ValueError("Invalid EFFECTIVENESS_COMPUTE_RECALL. Must be True or False.")
        self._set_validated("EFFECTIVENESS_COMPUTE_RECALL", "TRUE" if value else "FALSE")

    def set_effectiveness_recalls_to_compute(self, values: list[int]) -> None:
        """
        Define which recall values should be computed.

        Args:
            values (list[int]): list of positive integers (e.g., [1, 2, 5, 10, 15]).

        Raises:
            ValueError: if list is empty or contains non-positive integers.
        """
        if (
            not isinstance(values, list)
            or not values
            or not all(isinstance(v, int) and v > 0 for v in values)
        ):
            raise ValueError(
                "Invalid EFFECTIVENESS_RECALLS_TO_COMPUTE. Must be a non-empty list of positive integers."
            )
        value_str = ",".join(str(v) for v in values)
        self._set_validated("EFFECTIVENESS_RECALLS_TO_COMPUTE", value_str)

    def set_effectiveness_precisions_to_compute(self, values: list[int]) -> None:
        """
        Define which precision values should be computed.

        Args:
            values (list[int]): list of positive integers (e.g., [1, 2, 5, 10, 15]).

        Raises:
            ValueError: if list is empty or contains non-positive integers.
        """
        if (
            not isinstance(values, list)
            or not values
            or not all(isinstance(v, int) and v > 0 for v in values)
        ):
            raise ValueError(
                "Invalid EFFECTIVENESS_PRECISIONS_TO_COMPUTE. Must be a non-empty list of positive integers."
            )
        value_str = ",".join(str(v) for v in values)
        self._set_validated("EFFECTIVENESS_PRECISIONS_TO_COMPUTE", value_str)


    def set_rk_format(self, value: str) -> None:
        """
        Define the ranked list input format.

        Args:
            value (str): format of the input ranked list.
                         Must be either 'NUM' (numeric) or 'STR' (string).
        """
        self._set_validated("INPUT_RK_FORMAT", value)

    def set_input_matrix_type(self, value: str) -> None:
        """
        Define the type of the input matrix.

        Args:
            value (str): type of the matrix.
                         Must be either 'DIST' (distance) or 'SIM' (similarity).
        """
        self._set_validated("INPUT_MATRIX_TYPE", value)

    def set_matrix_to_rk_sorting(self, value: str) -> None:
        """
        Define the sorting algorithm used when converting a matrix into ranked lists.

        Args:
            value (str): sorting method.
                         Must be either 'HEAP' or 'INSERTION'.
        """
        self._set_validated("MATRIX_TO_RK_SORTING", value)

    def set_input_files(self, value):
        """
        Set the input files.

        Accepts:
            - str: path to a single file.
            - list[str]: multiple file paths (fusion).
            - list[list]: ranked lists to be written to disk.

        Raises:
            TypeError: if value type is unsupported.
            ValueError: if list is empty or contains invalid paths.
        """
        if not isinstance(value, (str, list)):
            raise TypeError(
                f"Invalid input type for set_input_files: {type(value)}. "
                "Must be str, list[str], or list[list]."
            )

        self.input_files_list = value

        # Case 1: list input
        if isinstance(value, list):
            if len(value) == 0:
                raise ValueError("Input file list cannot be empty.")

            # Case 1a: list of lists -> write them as files first
            if isinstance(value[0], list):
                aux = os.path.dirname(self.config_path)
                data_paths = configGenerator.write_input_files(self.input_files_list, aux)
                self.set_input_files(data_paths)
                return

            # Case 1b: list of strings -> validate each path
            if not all(isinstance(elem, str) for elem in value):
                raise TypeError("All elements of input_files_list must be strings.")

            for elem in value:
                validate_path(elem, must_exist=True)

        # Case 2: single string -> validate directly
        if isinstance(value, str):
            validate_path(value, must_exist=True)

        # Delegate to configGenerator (it will set UDL_TASK and INPUT_FILE_FORMAT)
        configGenerator.set_input(value, self.parameters, self.list_parameters)
   
    
    def set_ranked_lists_size(self, value):
        """
        Set ALL ranked lists sizes at once.

        Special case: updates multiple parameters (all *_L).

        Args:
            value (int): size of ranked lists. Must be a positive integer.
        """
        if not isinstance(value, int) or value <= 0:
            raise ValueError(
                f"Invalid ranked list size: {value}. Must be a positive integer."
            )

        configGenerator.set_all_ranked_lists_size(
            value, self.parameters, self.list_parameters
        )    

    def set_dataset_size(self, value: int) -> None:
        """
        Set the dataset size.

        Args:
            value (int): total number of elements in the dataset.
        """
        if not isinstance(value, int) or value <= 0:
            raise ValueError(
                f"Invalid dataset size: {value}. Must be a positive integer."
            )
        self._set_validated("SIZE_DATASET", value)

    def set_lists_file(self, value: str) -> None:
        """
        Set the path to the input file list.

        Args:
            value (str): path to the file list.
        """
        # if not isinstance(value, str) or not value.strip():
        #     raise ValueError("Invalid lists file path. Must be a non-empty string.")
        # self._set_validated("INPUT_FILE_LIST", value)
        path_str = validate_path(value, must_exist=True)
        self._set_validated("INPUT_FILE_LIST", path_str)

    def set_classes_file(self, value: str) -> None:
        """
        Set the path to the classes file.

        Args:
            value (str): path to the classes file.
        """
        path_str = validate_path(value, must_exist=True)
        self._set_validated("INPUT_FILE_CLASSES", path_str)

    def set_output_log_file_path(self, value: str) -> None:
        """
        Set the path of the output log.

        Args:
            value (str): path to the log file.
        """
        path_str = validate_path(value, must_exist=False)
        self._set_validated("OUTPUT_LOG_FILE_PATH", path_str)
        

    def add_new_parameter(self, param: str, value) -> None:
        """
        Add a completely new parameter to the config.

        Args:
            param (str): parameter name (must not be empty).
            value: parameter value.
        """
        if not isinstance(param, str) or not param.strip():
            raise ValueError("Parameter name must be a non-empty string.")
        configGenerator.new_parameters(
            param, value, self.parameters, self.list_parameters
        )

    def add_input_files(self, value) -> None:
        """
        Add new input files in fusion mode.

        Args:
            value (str | list): new file(s) to add.
        """
        if not isinstance(value, (str, list)):
            raise TypeError(
                f"Invalid type for input files: {type(value)}. Must be str or list."
            )
        configGenerator.new_fusion_parameter(
            value, self.parameters, self.list_parameters
        )

    def set_input_images_path(self, value: str) -> None:
        """
        Set the path to the input images.

        Args:
            value (str): path to the images directory.
        """
        path_str = validate_path(value, must_exist=True)
        self._set_validated("INPUT_IMAGES_PATH", path_str)

    def set_param(self, param: str, value) -> None:
        """
        Change the value of an existing parameter.

        Args:
            param (str): name of the parameter to change (must exist).
            value: new value for the parameter.
        """
        if not isinstance(param, str) or not param.strip():
            raise ValueError("Parameter name must be a non-empty string.")
        configGenerator.setParameter(param, value, self.parameters)
    
    def set_method_parameters(self, method: str, **kwargs) -> None:
        """
        Set multiple parameters for a specific UDLF method in one call.

        This function allows configuring all parameters related to a given method
        (e.g., CPRR, RFE, RDPAC) at once. Missing parameters are automatically
        filled with their default values, as defined in METHOD_PARAMS.

        Args:
            method (str): the method name (e.g., "CPRR", "RFE", "RDPAC").
            **kwargs: key-value pairs of parameters specific to the method.
                The keys must match the shorthand names defined in METHOD_PARAMS.

                Example:
                    set_method_parameters("CPRR", k=10, alpha=0.5)

        Raises:
            ValueError: if the method is not supported, or if an invalid parameter
                        name is provided in kwargs.
        """
        method = method.upper()
        if method not in METHOD_PARAMS:
            raise ValueError(f"Unsupported method: {method}")

        param_map = METHOD_PARAMS[method]

        # for key, spec in param_map.items():
        #     if key in kwargs:
        #         value = kwargs[key]
        #     else:
        #         value = spec.get("default")
        #     self._set_validated(spec["param"], value)
        for key, spec in param_map.items():
            if key in kwargs:
                value = kwargs[key]
            else:
                value = spec.get("default")

            # type verification
            expected_type = spec.get("type")
            if expected_type is not None and not isinstance(value, expected_type):
                raise ValueError(
                    f"Invalid type for parameter '{key}' in method {method}. "
                    f"Expected {expected_type.__name__}, got {type(value).__name__}."
                )

            self._set_validated(spec["param"], value)

        logger.debug("Parameters for method %s set: %r", method, kwargs)


    def get_param(self, param: str):
        """
        Get the value of a parameter.

        Args:
            param (str): name of the parameter to retrieve.

        Returns:
            The parameter value.
        """
        if not isinstance(param, str) or not param.strip():
            raise ValueError("Parameter name must be a non-empty string.")
        return configGenerator.getParameter(param, self.parameters)

    def write_config(self, path: str = "new_config.ini") -> None:
        """
        Write the current configuration to a file.

        Args:
            path (str): path to the new config file. Must be a non-empty string
                        and should end with '.ini'.
        """
        if not isinstance(path, str) or not path.strip():
            raise ValueError("Config file path must be a non-empty string.")
        if not path.endswith(".ini"):
            raise ValueError("Config file path must end with '.ini'.")
        configGenerator.writeConfig(
            self.parameters, self.list_parameters, path
        )

    def list_parameters_names(self) -> None:
        """
        Display parameter names (without values).
        """
        configGenerator.listParameters(self.list_parameters)

    def list_param_full(self) -> None:
        """
        Display all parameters with values and comments (detailed view).
        """
        configGenerator.list_config_full(
            self.parameters, self.list_parameters
        )

    def list_param(self) -> None:
        """
        Display all parameters with values only (no comments).
        """
        configGenerator.list_config(
            self.parameters, self.list_parameters
        )

    def list_param_info(self, param: str) -> None:
        """
        Display detailed information about a specific parameter,
        including its value and comments.

        Args:
            param (str): name of the parameter.
        """
        if not isinstance(param, str) or not param.strip():
            raise ValueError("Parameter name must be a non-empty string.")
        configGenerator.list_parameter_info(
            self.parameters, self.list_parameters, param
        )

    def list_method_info(self, method: str) -> None:
        """
        Display information about a specific UDL method.

        Args:
            method (str): method name.
        """
        if not isinstance(method, str) or not method.strip():
            raise ValueError("Method name must be a non-empty string.")
        configGenerator.list_info_selected_method(
            method, self.parameters, self.list_parameters
        )

    def get_method_name(self):
        """
        Get the current UDL method.

        Returns:
            str | list: the configured method(s).
        """
        return configGenerator.getParameter("UDL_METHOD", self.parameters)

    def get_task(self):
        """
        Get the current UDL task type (UDL or FUSION).

        Returns:
            str: the configured task type.
        """
        return configGenerator.getParameter("UDL_TASK", self.parameters)

    def get_classes_file(self):
        """
        Get the path to the classes file.

        Returns:
            str: path to the classes file.
        """
        return configGenerator.getParameter("INPUT_FILE_CLASSES", self.parameters)

    def get_lists_file(self):
        """
        Get the path to the input file list.

        Returns:
            str: path to the file list.
        """
        return configGenerator.getParameter("INPUT_FILE_LIST", self.parameters)

    def get_dataset_size(self):
        """
        Get the dataset size.

        Returns:
            int: total number of elements in the dataset.
        """
        return configGenerator.getParameter("SIZE_DATASET", self.parameters)

    def get_output_log_file(self):
        """
        Get the path of the output log file.

        Returns:
            str: path to the log file.
        """
        return configGenerator.getParameter("OUTPUT_LOG_FILE_PATH", self.parameters)

    def get_input_files(self):
        """
        Get the configured input files.

        Returns:
            str | list[str]: path(s) to the input file(s).
                            - str if UDL task
                            - list[str] if FUSION task
        """
        return configGenerator.get_input_files_parameters(
            self.parameters, self.list_parameters
        )

    def get_output_file_format(self):
        """
        Get the output file format.

        Returns:
            str: output format (e.g., 'RK' or 'MATRIX').
        """
        return configGenerator.getParameter("OUTPUT_FILE_FORMAT", self.parameters)

    def get_output_matrix_type(self):
        """
        Get the output matrix type.

        Returns:
            str: output matrix type ('DIST' or 'SIM').
        """
        return configGenerator.getParameter("OUTPUT_MATRIX_TYPE", self.parameters)

    def get_output_rk_format(self):
        """
        Get the output ranked list format.

        Returns:
            str: output ranked list format ('NUM', 'STR', 'HTML', 'ALL').
        """
        return configGenerator.getParameter("OUTPUT_RK_FORMAT", self.parameters)

    def get_output_file_path(self):
        """
        Get the base path of the output file.

        Returns:
            str: path where output will be saved (without extension).
        """
        return configGenerator.getParameter("OUTPUT_FILE_PATH", self.parameters)

    def get_input_matrix_type(self):
        """
        Get the input matrix type.

        Returns:
            str: input matrix type ('DIST' or 'SIM').
        """
        return configGenerator.getParameter("INPUT_MATRIX_TYPE", self.parameters)

    def get_input_rk_format(self):
        """
        Get the input ranked list format.

        Returns:
            str: input ranked list format ('NUM' or 'STR').
        """
        return configGenerator.getParameter("INPUT_RK_FORMAT", self.parameters)

    def get_matrix_to_rk_sorting(self):
        """
        Get the sorting method used to convert matrices into ranked lists.

        Returns:
            str: sorting method ('HEAP' or 'INSERTION').
        """
        return configGenerator.getParameter("MATRIX_TO_RK_SORTING", self.parameters)

    def get_input_images_path(self):
        """
        Get the path to the input images.

        Returns:
            str: path to the images directory.
        """
        return configGenerator.getParameter("INPUT_IMAGES_PATH", self.parameters)

    def show_input_rk(self, line: int, rk_size: int = 10,
                    images_shape: tuple[int, int] = (0, 0),
                    start_element: int = 0,
                    fusion_index: int = 1):
        """
        Show an input ranked list (before processing) as concatenated images.

        Args:
            line (int): line index in the ranked list file (query index).
            rk_size (int): number of retrieved elements to show.
            images_shape (tuple[int, int]): resize shape (w,h). If (0,0), use min size.
            start_element (int): starting index offset for the ranked list.
            fusion_index (int): index of fusion input file (only used when task=FUSION).

        Returns:
            PIL.Image.Image: the combined image for visualization.
        """
        # --- Detect task type ---
        task = self.get_task()[0]

        if task == "FUSION":
            logger.warning(
                "Task is set to FUSION. Showing ranked list from INPUT_FILES_FUSION_%d",
                fusion_index,
            )
            rk_path = self.parameters.get(f"INPUT_FILES_FUSION_{fusion_index}")[0]
            if rk_path is None:
                raise ValueError(f"No fusion input file found for index {fusion_index}")
        else:
            rk_path = self.parameters.get("INPUT_FILE")[0]

        list_path = self.get_lists_file()[0]
        classes_path = self.get_classes_file()[0]
        images_path = self.get_input_images_path()[0]

        #print(rk_path, list_path, classes_path, images_path)
        # --- Validate presence and existence ---
        paths = {
            "INPUT_FILE (ranked list)": (rk_path, Path(rk_path).is_file() if rk_path else False),
            "INPUT_FILE_LIST": (list_path, Path(list_path).is_file() if list_path else False),
            "INPUT_FILE_CLASSES": (classes_path, Path(classes_path).is_file() if classes_path else False),
            "INPUT_IMAGES_PATH": (images_path, Path(images_path).is_dir() if images_path else False),
        }

        for name, (p, exists) in paths.items():
            if not p or not isinstance(p, str):
                raise ValueError(f"{name} is not defined or not a valid string: {p}")
            if not exists:
                raise FileNotFoundError(f"{name} does not exist at: {p}")

        return render_ranked_list(
            rk_path=rk_path,
            list_path=list_path,
            classes_path=classes_path,
            images_path=images_path,
            line=line,
            rk_size=rk_size,
            images_shape=images_shape,
            save=False,
            start_element=start_element
        )

 
    # def show_input_rk(self, line: int, rk_size: int = 10,
    #                 images_shape: tuple[int, int] = (0, 0),
    #                 start_element: int = 0):
    #     """
    #     Show an input ranked list (before processing) as concatenated images.

    #     Args:
    #         line (int): line index in the ranked list file (query index).
    #         rk_size (int): number of retrieved elements to show.
    #         images_shape (tuple[int, int]): resize shape (w,h). If (0,0), use min size.
    #         start_element (int): starting index offset for the ranked list.

    #     Returns:
    #         PIL.Image.Image: the combined image for visualization.
    #     """
    #     rk_path = self.parameters.get("INPUT_FILE")[0]
    #     list_path = self.get_lists_file()[0]
    #     classes_path = self.get_classes_file()[0]
    #     images_path = self.get_input_images_path()[0]
    #     print(rk_path, list_path, classes_path, images_path)

    #     # --- Validate presence and existence ---
    #     paths = {
    #         "INPUT_FILE (ranked list)": (rk_path, Path(rk_path).is_file() if rk_path else False),
    #         "INPUT_FILE_LIST": (list_path, Path(list_path).is_file() if list_path else False),
    #         "INPUT_FILE_CLASSES": (classes_path, Path(classes_path).is_file() if classes_path else False),
    #         "INPUT_IMAGES_PATH": (images_path, Path(images_path).is_dir() if images_path else False),
    #     }

    #     for name, (p, exists) in paths.items():
    #         if not p or not isinstance(p, str):
    #             raise ValueError(f"{name} is not defined or not a valid string: {p}")
    #         if not exists:
    #             raise FileNotFoundError(f"{name} does not exist at: {p}")

    #     return render_ranked_list(
    #         rk_path=rk_path,
    #         list_path=list_path,
    #         classes_path=classes_path,
    #         images_path=images_path,
    #         line=line,
    #         rk_size=rk_size,
    #         images_shape=images_shape,
    #         save=False,
    #         start_element=start_element
    #     )