import os
from pyUDLF.utils import configGenerator
from pyUDLF import run_calls


# interface pro configGenerator
#    parameters = dict()  # init
#    list_parameters = dict()
# config_path = "/home/gustavo/Desktop/UDLF/UDLF/bin/config.ini"


class InputType:
    """
    Class to handle the inputs
    """

    def __init__(self, config_path=None, input_files=None):
        """
        Initial class parameters.
        """
        self.parameters = dict()
        self.list_parameters = []
        self.input_files_list = input_files
        self.config_path = config_path

        if self.config_path is None:
            self.config_path = run_calls.config_path
            if not os.path.isfile(self.config_path):
                print("Config is missing! Unable to initialize inputtype")
            run_calls.verify_bin(self.config_path, run_calls.bin_path)
            print("Class inicialization sucessful!")

        aux = self.init_parameters(self.config_path)
        if aux is None:
            return

        if input_files is not None:
            self.init_data()

    def init_parameters(self, path):
        """
        Start the parameters by reading the config

        Parameters:
            path -> config path that will be read
        """
        self.parameters, self.list_parameters = configGenerator.initParameters(
            path, self.parameters, self.list_parameters)
        if self.parameters is None:
            return None

    def init_data(self):
        data_paths = []
        # se for string -> eh o path
        # se for list["",""]-> eh strings pro fusion
        # se for list[ [rks1], [rks2] ] -> eh o arquivo, escrever e passar o path

        if isinstance(self.input_files_list, str):  # path
            # vai escrever o path e colocar auto no format
            self.set_input_files(self.input_files_list)

        if isinstance(self.input_files_list, list):
            # list de strs, ou seja, lista de paths
            if isinstance(self.input_files_list[0], str):
                self.set_input_files(self.input_files_list)

            # list de list -> ou seja, precisa escrever
            if isinstance(self.input_files_list[0], list):
                aux = os.path.dirname(self.config_path)
                data_paths = configGenerator.write_input_files(
                    self.input_files_list, aux)
                self.set_input_files(data_paths)

    def set_method_name(self, value):
        """
        Set the method to be used

        Parameters:
            value -> new method value
        """
        configGenerator.setParameter("UDL_METHOD", value, self.parameters)

    def set_task(self, value):
        """
        Set the method to be used

        Parameters:
            value -> new method value
        """
        configGenerator.setParameter("UDL_TASK", value, self.parameters)

    def set_output_file_format(self, value):
        """
        Set the output format

        Parameters:
            value -> new method value
        """
        configGenerator.setParameter(
            "OUTPUT_FILE_FORMAT", value, self.parameters)

    def set_output_matrix_type(self, value):
        """
        Set the output matrix type

        Parameters:
            value -> new method value
        """
        configGenerator.setParameter(
            "OUTPUT_MATRIX_TYPE", value, self.parameters)

    def set_output_rk_format(self, value):
        """
        Set the output ranked list format

        Parameters:
            value -> new method value
        """
        configGenerator.setParameter(
            "OUTPUT_RK_FORMAT", value, self.parameters)

    def set_output_file_path(self, value):
        """
        Set the path of the output

        Parameters:
            value -> new method value
        """
        configGenerator.setParameter(
            "OUTPUT_FILE_PATH", value, self.parameters)

    def set_rk_format(self, value):
        """
        """
        configGenerator.setParameter("INPUT_RK_FORMAT", value, self.parameters)

    def set_input_matrix_type(self, value):
        """
        """
        configGenerator.setParameter(
            "INPUT_MATRIX_TYPE", value, self.parameters)

    def set_input_files(self, value):
        """
        """
        self.input_files_list = value
        if isinstance(self.input_files_list, list):
            if isinstance(self.input_files_list[0], list):
                aux = os.path.dirname(self.config_path)
                data_paths = configGenerator.write_input_files(
                    self.input_files_list, aux)
                self.set_input_files(data_paths)
                return
        configGenerator.set_input(value, self.parameters, self.list_parameters)

    def set_ranked_lists_size(self, value):
        """
        Set ALL ranked lists sizes!
        """
        configGenerator.set_all_ranked_lists_size(
            value, self.parameters, self.list_parameters)

    def set_dataset_size(self, value):
        """
        """
        configGenerator.setParameter("SIZE_DATASET", value, self.parameters)

    def set_lists_file(self, value):
        """
        """
        configGenerator.setParameter("INPUT_FILE_LIST", value, self.parameters)

    def set_classes_file(self, value):
        """
        """
        configGenerator.setParameter(
            "INPUT_FILE_CLASSES", value, self.parameters)

    def set_output_log_file(self, value):
        """
        Set path of the output log
        """
        configGenerator.setParameter(
            "OUTPUT_LOG_FILE_PATH", value, self.parameters)

    def add_new_parameter(self, param, value):
        """
        """
        configGenerator.new_parameters(
            param, value, self.parameters, self.list_parameters)

    def add_input_files(self, value):
        """
        """
        configGenerator.new_fusion_parameter(
            value, self.parameters, self.list_parameters)

    def set_input_rk_format(self, value):
        """
        """
        configGenerator.setParameter("INPUT_RK_FORMAT", value, self.parameters)

    def set_matrix_to_rk_sorting(self, value):
        """
        """
        configGenerator.setParameter(
            "MATRIX_TO_RK_SORTING", value, self.parameters)

    def set_input_images_path(self, value):
        """
        """
        configGenerator.setParameter(
            "INPUT_IMAGES_PATH", value, self.parameters)

    def set_param(self, param, value):
        """
        Change the value of some parameter
        The parameter must exist

        Parameters:
            param -> parameter to be changed
            value -> new value
        """
        configGenerator.setParameter(param, value, self.parameters)

    def get_param(self, param):
        """
        Get parameter value

        Parameters:
            param -> parameter to get the value

        Return:
            parameter value
        """
        return configGenerator.getParameter(param, self.parameters)

    def write_config(self, path="new_config.ini"):  # path precisa do nome
        """
        Write new config

        Parameters:
            path -> path with the name of the new config
        """
        configGenerator.writeConfig(
            self.parameters, self.list_parameters, path)

    def list_parameters_names(self):
        """
        Displays parameters without values
        """
        configGenerator.listParameters(self.list_parameters)

    def list_param_full(self):
        """
        Displays parameters with values and information
        """
        configGenerator.list_config_full(
            self.parameters, self.list_parameters)

    def list_param(self):
        """
        Displays parameters with values and without information
        """
        configGenerator.list_config(self.parameters, self.list_parameters)

    def list_param_info(self, param):
        """
        Displays parameter with values and information
        """
        configGenerator.list_parameter_info(
            self.parameters, self.list_parameters, param)

    def list_method_info(self, method):
        """
        """
        configGenerator.list_info_selected_method(
            method, self.parameters, self.list_parameters)

    def get_method_name(self):
        """
        """
        return configGenerator.getParameter("UDL_METHOD", self.parameters)

    def get_task(self):
        """
        """
        return configGenerator.getParameter("UDL_TASK", self.parameters)

    def get_classes_file(self):
        """
        """
        return configGenerator.getParameter("INPUT_FILE_CLASSES", self.parameters)

    def get_lists_file(self):
        """
        """
        return configGenerator.getParameter("INPUT_FILE_LIST", self.parameters)

    def get_dataset_size(self):
        """
        """
        return configGenerator.getParameter("SIZE_DATASET", self.parameters)

    def get_output_log_file(self):
        """
        """
        return configGenerator.getParameter("OUTPUT_LOG_FILE_PATH", self.parameters)

    def get_input_files(self):
        """
        """
        return configGenerator.get_input_files_parameters(self.parameters, self.list_parameters)

    def get_output_file_format(self):
        """
        """
        return configGenerator.getParameter("OUTPUT_FILE_FORMAT", self.parameters)

    def get_output_matrix_type(self):
        """
        """
        return configGenerator.getParameter("OUTPUT_MATRIX_TYPE", self.parameters)

    def get_output_rk_format(self):
        """
        """
        return configGenerator.getParameter("OUTPUT_RK_FORMAT", self.parameters)

    def get_output_file_path(self):
        """
        """
        return configGenerator.getParameter("OUTPUT_FILE_PATH", self.parameters)

    def get_input_matrix_type(self):
        """
        """
        return configGenerator.getParameter("INPUT_MATRIX_TYPE", self.parameters)

    def get_input_rk_format(self):
        """
        """
        return configGenerator.getParameter("INPUT_RK_FORMAT", self.parameters)

    def get_matrix_to_rk_sorting(self):
        """
        """
        return configGenerator.getParameter("MATRIX_TO_RK_SORTING", self.parameters)

    def get_input_images_path(self):
        """
        """
        return configGenerator.getParameter("INPUT_IMAGES_PATH", self.parameters)
