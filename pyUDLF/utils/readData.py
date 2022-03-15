
def read_config(path):
    """
    Read config and return the parameters

    Parameters:
        path -> config path to read

    Returns:
        parameters -> dictionary with parameters and values
        list_parameters -> list with parameters
    """
    parameters = dict()
    list_parameters = []

    with open(path, 'r') as f:
        lines = [x.strip() for x in f.readlines()]
        lines = [x.split('=') for x in lines]

    for line in lines:
        if len(line) >= 2:
            param = line[0].strip()
            # value = line[1].split('#')[0]  # pega sem os comentarios
            value = line[1].split('#')     # teste para pegar os comentarios
            parameters[param] = value
            list_parameters.append(param)

    return parameters, list_parameters


def read_log(path):
    """
    Read config results and return 

    Parameters:
        path -> log path to read, same as config path

    Returns:
        log_parameters -> dictionary with results
    """
    log_parameters = dict()
    before = []
    after = []
    gains = []
    parametros = []
    metodo = "NONE"

    with open(path, 'r') as f:
        lines = [x.strip() for x in f.readlines()]

        for i in range(len(lines)):
            if "Task" in lines[i]:
                line = lines[i].split(':')
                metodo = line[1].strip()

            if "Time" in lines[i]:
                line = lines[i].split(':')
                log_parameters["Time"] = line[1]

            if metodo == "FUSION":
                if "Effectiveness" in lines[i]:
                    i = i + 1
                    while("-" not in lines[i]):
                        line = lines[i].split()
                        parametros.append(line[0])
                        before.append(line[1])
                        i = i + 1
                    j = 0
                    for j in range(len(parametros)):
                        log_parameters[parametros[j]] = before[j]

            else:
                if "Before" in lines[i]:
                    i = i + 1
                    while ("After" not in lines[i]):
                        line = lines[i].split()
                        parametros.append(line[0])
                        before.append(line[1])
                        # log_parameters[line[0]] = line[1]
                        i = i + 1

                    i = i + 1
                    while ("Relative Gains" not in lines[i]):
                        line = lines[i].split()
                        after.append(line[1])
                        i = i + 1

                    i = i + 1
                    j = 0
                    while (j < len(parametros)):
                        line = lines[i].split()
                        gains.append(line[1])
                        i = i + 1
                        j = j + 1

                    j = 0
                    for j in range(len(parametros)):
                        log_parameters[parametros[j]] = dict(
                            [("Before", before[j]),
                             ("After", after[j]),
                             ("Gain", gains[j])])
    return log_parameters


def read_ranked_lists_file_numeric(file_path, top_k=1000):
    """
    Read numeric ranked list and return it

    Parameters:
        file_path -> numeric ranked list path
        top_k -> ranked list size

    Returns:
        returns a ranked list with image numbers
    """
    print("\n\tReading file..", file_path)
    with open(file_path, "r") as f:
        return [[int(y) for y in x.strip().split(" ")][:top_k]
                for x in f.readlines()]


def read_ranked_lists_file_string(file_path, top_k=1000):
    """
    Read string ranked list and return it

    Parameters:
        file_path -> string ranked list path
        top_k -> ranked list size

    Returns:
        returns a ranked list of image names
    """
    print("\n\tReading file..", file_path)
    with open(file_path, "r") as f:
        return [[y for y in x.strip().split(" ")][:top_k]
                for x in f.readlines()]


def read_matrix_file(file_path):
    """
    Read matrix file and return it

    Parameters:
        file_path -> matrix file path

    Returns:
        returns a matrix 
    """
    print("\n\tReading file", file_path)
    with open(file_path, "r") as f:
        return [[float(y) for y in x.strip().split(" ")]
                for x in f.readlines()]
