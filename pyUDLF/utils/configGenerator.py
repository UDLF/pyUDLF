from pyUDLF.utils import readData
from pyUDLF.utils import writeData
import os.path
import re


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


def write_input_files(data, path):
    data_paths = []
    cont = 1
    for i in range(len(data)):
        temp = os.path.join("/rks_", cont)
        aux = os.path.join(path, temp)
        while os.path.isfile(aux):
            cont = cont + 1
            temp = os.path.join("/rks_", cont)
            aux = os.path.join(path, temp)

        data_paths.append(aux)
        writeData.write_data(data[i], data_paths[i])
        cont = cont+1

    # print(data_paths)
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
                aux = "INPUT_FILES_FUSION_{}".format(i+1)
                if aux in list_parameters:
                    setParameter(
                        aux, value[i], parameters)
                else:
                    new_parameters(
                        aux, value[i], parameters, list_parameters)


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
    """
    i = 1
    fusion_files = []
    flag = True
    task = getParameter("UDL_TASK", parameters)
    task = task[0].strip()
    if task == "UDL":
        return getParameter("INPUT_FILE", parameters)[0].strip()
    if task == "FUSION":
        while (flag):
            aux = "INPUT_FILES_FUSION_{}".format(i)
            if aux in list_parameters:
                fusion_files.append(getParameter(aux, parameters)[0].strip())
            else:
                flag = False
            i = i + 1
        return fusion_files


def new_fusion_parameter(value, parameters, list_parameters):
    """
    """
    if (parameters["UDL_TASK"][0] == "UDL"):
        print("ERROR, not fusion")
        return

    i = 0
    if isinstance(value, str):
        tam = 1
        aux_value = [value]
    elif isinstance(value, list):
        aux_value = value
        tam = len(value)
    else:
        print("Type Error !")
        return

    cont = 0

    while (i < tam):
        aux = "INPUT_FILES_FUSION_{}".format(cont+1)
        cont = cont + 1

        if (aux not in list_parameters):
            new_parameters(aux, aux_value[i], parameters, list_parameters)
            i = i + 1
            # print(parameters[aux])


def list_info_selected_method(method, parameters, list_parameters):
    aux = "PARAM_{}".format(method.upper())
    print("...Listing {} information...".format(method.upper()))
    for i in range(len(parameters)):
        if aux in list_parameters[i]:
            print("{} = {} #{}".format(list_parameters[i],
                  parameters[list_parameters[i]][0], parameters[list_parameters[i]][1]))
