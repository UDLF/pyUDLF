from pyUDLF.utils import readData
from pyUDLF.utils import writeData
import os.path
import re
import tempfile


def initParameters(config_path, parameters, list_parameters):
    """
    Initialize the parameters

    Parameters:
        config_path -> config path
        parameters -> dictionary to receive the parameters and values
        list_parameters -> list to receive the parameters

    Returns:
        parameters -> dictionary with parameters and values
        list_parameters -> list with parameters
    """
    try:
        parameters, list_parameters = readData.read_config(config_path)
    except:
        print("ERROR, could not initialize inputType")
        print("Invalid config!")
        return dict(), []

    return parameters, list_parameters


def write_input_files(data, path=None):
    """
    Write in-memory ranked lists to text files that UDLF can read.

    Parameters:
        data -> list of ranked lists matrices (one per input file); each matrix
                is a list of rows (or a 2D numpy array) of image indices
        path -> directory for the files; a new temporary directory if None

    Returns:
        data_paths -> list with the path of each written file
    """
    if path is None:
        path = tempfile.mkdtemp(prefix="pyudlf_inputs_")
    os.makedirs(path, exist_ok=True)

    data_paths = []
    cont = 1
    for matrix in data:
        aux = os.path.join(path, f"rks_{cont}.txt")
        while os.path.isfile(aux):
            cont = cont + 1
            aux = os.path.join(path, f"rks_{cont}.txt")

        writeData.write_data(matrix, aux)
        data_paths.append(aux)
        cont = cont + 1

    return data_paths


def setParameter(param, value, parameters):
    """
    Set parameters value

    Parameters:
        param -> parameter to assign new value
        value -> value to assign
        parameters -> dictionary with parameters and values

    Returns:
        Sucess or error message
    """
    param = param.upper().strip()
    
    if param in parameters:
        aux = getParameter(param, parameters)

        # print(aux)
        parameters[param][0] = str(value)

        if(len(aux)) > 1:
            parameters[param][1] = aux[1]
        # print("{} insert with sucess".format(param))
    else:
        print("{} does not exist in parameters!".format(param))


def getParameter(param, parameters):
    """
    Get parameter value

    Parameters:
        param -> parameter to get the value
        parameters -> dictionary with parameters and values

    Return:
        parameter value
    """
    param = param.upper().strip()
    if param in parameters:
        return parameters[param]
    else:
        print("{} does not exist in parameters!".format(param))


def new_parameters(param, value, parameters, list_parameters):
    """
    Add a new parameter

    Parameters:
        param ->
        value ->
        parameters ->
        list_parameters ->

    Return:
        Updated dictionary and list
    """
    param = param.upper().strip()
    if param not in list_parameters:
        list = [value]
        parameters[param] = list
        list_parameters.append(param)
    else:
        print("Parameters already exist")


def writeConfig(parameters, list_parameters, path="new_config.ini"):
    """
    Write new config

    Parameters:
        parameters -> dictionary with parameters and values
        list_parameters -> list of parameters in config order
        path -> path with the name of the new config
    """
    f = open(path, "w+")
    for param in list_parameters:
        # print("{}={}".format(param, parameters[param]), file=f)
        if len(parameters[param]) > 1:
            f.write("{:<37} = {:<15} #{:<30}\n".format(
                param, parameters[param][0].strip(), parameters[param][1]))
        else:
            f.write("{:<37} = {:<15}\n".format(
                param, parameters[param][0].strip()))

    f.close()


def listParameters(list_parameters):
    """
    Displays parameters without values

    Parameters:
        list_parameters -> list of parameters in config order
    """
    print("\n...Listing parameters withou values and comments...\n")
    for param in list_parameters:
        print(param)


def list_config_full(parameters, list_parameters):
    """
    Display the parameters with the comments

    Parameters:
        parameters ->  dictionary with parameters and values
        list_parameters -> list of parameters in config order
    """
    print("\n...Listing parameters with values and comments...\n")
    for param in list_parameters:
        if len(parameters[param]) < 2:
            print("{} = {} #----".format(param, parameters[param][0].strip()))
        else:
            print("{} = {} #{}".format(
                param, parameters[param][0].strip(), parameters[param][1]))


def list_config(parameters, list_parameters):
    """
    Displays parameters with values

    Parameters:
        parameters ->  dictionary with parameters and values
        list_parameters -> list of parameters in config order
    """
    print("\n...Listing parameters with values and withou comments...\n")
    for param in list_parameters:
        print("{} = {}".format(param, parameters[param][0].strip()))


def list_parameter_info(parameters, list_parameters, param):
    """
    Display the parameter with the comment

    Parameters:
        param -> parameter to display
        parameters ->  dictionary with parameters and values
        list_parameters -> list of parameters in config order
    """

    if param in list_parameters:
        # print("\n...Listing parameter info!...\n")
        if len(parameters[param]) < 2:
            print("{} = {} ".format(
                param, parameters[param][0].strip()))
        else:
            print("{} = {} #{}".format(
                param, parameters[param][0].strip(), parameters[param][1]))
    else:
        print("Parameters not found!..")


def set_input(value, parameters, list_parameters):
    setParameter("INPUT_FILE_FORMAT", "AUTO", parameters)

    if isinstance(value, str):
        setParameter("UDL_TASK", "UDL", parameters)
        setParameter("INPUT_FILE", value, parameters)

    if isinstance(value, list):
        if len(value) < 2:
            setParameter("UDL_TASK", "UDL", parameters)
            setParameter("INPUT_FILE", value[0], parameters)
        else:
            setParameter(
                "UDL_TASK", "FUSION", parameters)
            for i in range(len(value)):
                _set_or_add("INPUT_FILES_FUSION_{}".format(i+1), value[i],
                            parameters, list_parameters)
            # UDLF only reads the first NUM_INPUT_FUSION_FILES files
            _set_or_add("NUM_INPUT_FUSION_FILES", len(value), parameters, list_parameters)


def _set_or_add(param, value, parameters, list_parameters):
    """Set a parameter, adding it to the config if it does not exist yet."""
    if param in parameters:
        setParameter(param, value, parameters)
    else:
        new_parameters(param, str(value), parameters, list_parameters)


def _num_fusion_files(parameters):
    try:
        return int(str(parameters["NUM_INPUT_FUSION_FILES"][0]).strip())
    except (KeyError, ValueError):
        return 0


def set_all_ranked_lists_size(value, parameters, list_parameters):
    """
    """
    for param in list_parameters:
        if(re.search(r'PARAM_[A-Z]*_L$', param)) is not None:
            if len(parameters[param]) < 2:
                parameters[param][0] = str(value)
            else:
                setParameter(param, value, parameters)


def get_input_files_parameters(parameters, list_parameters):
    """
    Return the input file (UDL task) or the list of input files (FUSION task).
    """
    fusion_files = []
    task = getParameter("UDL_TASK", parameters)
    task = task[0].strip()
    if task == "UDL":
        return getParameter("INPUT_FILE", parameters)[0].strip()
    if task == "FUSION":
        # only the first NUM_INPUT_FUSION_FILES are used by UDLF
        for i in range(1, _num_fusion_files(parameters) + 1):
            aux = "INPUT_FILES_FUSION_{}".format(i)
            if aux in list_parameters:
                fusion_files.append(getParameter(aux, parameters)[0].strip())
        return fusion_files


def new_fusion_parameter(value, parameters, list_parameters):
    """
    Append input files to a FUSION task (after the files already set).
    """
    if parameters["UDL_TASK"][0].strip() != "FUSION":
        raise ValueError("add_input_files requires UDL_TASK = FUSION. "
                         "Use set_input_files([file1, file2, ...]) first.")

    if isinstance(value, str):
        aux_value = [value]
    elif isinstance(value, list):
        aux_value = value
    else:
        raise TypeError(f"Invalid type for input files: {type(value)}")

    count = _num_fusion_files(parameters)
    for path in aux_value:
        count += 1
        _set_or_add("INPUT_FILES_FUSION_{}".format(count), path,
                    parameters, list_parameters)
    _set_or_add("NUM_INPUT_FUSION_FILES", count, parameters, list_parameters)


def list_info_selected_method(method, parameters, list_parameters):
    aux = "PARAM_{}".format(method.upper().strip())
    print("...Listing {} information...".format(method.upper()))
    for i in range(len(parameters)):
        if aux in list_parameters[i]:
            if len(parameters[list_parameters[i]]) > 2:
                print("{} = {} #{}".format(list_parameters[i],
                    parameters[list_parameters[i]][0], parameters[list_parameters[i]][1]))
            else:
                print("{} = {}".format(list_parameters[i],
                    parameters[list_parameters[i]][0]))
