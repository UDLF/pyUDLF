import os
#import logging
from pyUDLF.utils import configGenerator
from pyUDLF import run_calls
from pyUDLF.utils.logger import get_logger
from pyUDLF.utils.validations import validate_param


logger = get_logger(__name__)

#logger = logging.getLogger(__name__)

class InputType:
    """
    Class to handle the inputs
    """

    def __init__(self, config_path=None, input_files=None):
        """
        Initialize the class with optional config path and input files.
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
        Load parameters by reading the config file.

        Args:
            path (str): Path to the config file.

        Returns:
            bool: True if parameters loaded successfully, False otherwise.
        """
        self.parameters, self.list_parameters = configGenerator.initParameters(
            path, self.parameters, self.list_parameters)

        if not self.parameters:  # explicit check
            logger.error("Could not load parameters from config '%s'.", path)
            return False

        return True
    
    def init_data(self):
        """
        Initialize input data depending on the type of input_files_list.

        Cases:
            - str: a single file path.
            - list[str]: a list of file paths (fusion mode).
            - list[list]: lists of ranked lists (write them to disk before using).
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
        Validate and set a config parameter. Raises ValueError if invalid.
        """
        normalized = validate_param(key, value)
        configGenerator.setParameter(key, normalized, self.parameters)
        logger.debug("%s set to %r", key, normalized)

    def set_method_name(self, value: str) -> None:
        """
        Set the UDL method (e.g., NONE, CPRR, RFE).
        """
        self._set_validated("UDL_METHOD", value)

    def set_task(self, value: str) -> None:
        """
        Set the UDL task type (UDL or FUSION).
        """
        self._set_validated("UDL_TASK", value)

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
        if not isinstance(value, str) or not value.strip():
            raise ValueError("Invalid output file path. Must be a non-empty string.")
        configGenerator.setParameter("OUTPUT_FILE_PATH", value, self.parameters)
        logger.debug("OUTPUT_FILE_PATH set to %r", value)


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
        """
        if not isinstance(value, (str, list)):
            raise TypeError(
                f"Invalid input type for set_input_files: {type(value)}. "
                "Must be str, list[str], or list[list]."
            )

        self.input_files_list = value

        if isinstance(value, list):
            if len(value) == 0:
                raise ValueError("Input file list cannot be empty.")

            if isinstance(value[0], list):
                aux = os.path.dirname(self.config_path)
                data_paths = configGenerator.write_input_files(self.input_files_list, aux)
                self.set_input_files(data_paths)
                return

            if not all(isinstance(elem, str) for elem in value):
                raise TypeError("All elements of input_files_list must be strings.")

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
        if not isinstance(value, str) or not value.strip():
            raise ValueError("Invalid lists file path. Must be a non-empty string.")
        self._set_validated("INPUT_FILE_LIST", value)


    def set_classes_file(self, value: str) -> None:
        """
        Set the path to the classes file.

        Args:
            value (str): path to the classes file.
        """
        if not isinstance(value, str) or not value.strip():
            raise ValueError("Invalid classes file path. Must be a non-empty string.")
        self._set_validated("INPUT_FILE_CLASSES", value)

    def set_output_log_file(self, value: str) -> None:
        """
        Set the path of the output log.

        Args:
            value (str): path to the log file.
        """
        if not isinstance(value, str) or not value.strip():
            raise ValueError("Invalid log file path. Must be a non-empty string.")
        self._set_validated("OUTPUT_LOG_FILE_PATH", value)

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
        if not isinstance(value, str) or not value.strip():
            raise ValueError("Invalid images path. Must be a non-empty string.")
        self._set_validated("INPUT_IMAGES_PATH", value)

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
