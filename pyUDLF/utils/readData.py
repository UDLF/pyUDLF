import re


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

    for line in lines:
        # comment lines (even with '=' inside) are not parameters
        if line.startswith('#') or '=' not in line:
            continue
        name, rest = line.split('=', 1)
        param = name.strip()
        # [value, comment]: the comment after '#' is kept for display
        value = rest.split('#', 1)
        if param not in parameters:
            list_parameters.append(param)
        parameters[param] = value

    return parameters, list_parameters


def read_log(path):
    """
    Read a UDLF log file and return its results

    Parameters:
        path -> log path to read (OUTPUT_LOG_FILE_PATH)

    Returns:
        log_parameters -> dictionary with results
    """
    with open(path, 'r') as f:
        return parse_log(f.read())


def parse_log(text):
    """
    Parse the results of a UDLF log, given as text (the log file contents or
    everything UDLF printed, which ends with the log)

    Parameters:
        text -> log text

    Returns:
        log_parameters -> dictionary with results, as numbers:
            "Time": execution time in seconds
            UDL task: {"MAP": {"Before": 0.50, "After": 0.63, "Gain": 27.6}, "P@10": ...}
                      ("Gain" is the relative gain in percent)
            FUSION task: {"MAP": 0.63, "P@10": ...} (results after fusion)
    """
    log_parameters = dict()
    task = "UDL"
    section = None
    values = {"Before": {}, "After": {}, "Gain": {}}

    for raw in text.splitlines():
        line = raw.strip()

        match = _LOG_TASK.match(line)
        if match:
            task = match.group(1)
            continue

        match = _LOG_TIME.search(line)
        if match:
            log_parameters["Time"] = float(match.group(1))
            continue

        if line.startswith("Before:"):
            section = "Before"
        elif line.startswith("After:"):
            section = "After"
        elif line.startswith("Relative Gains:"):
            section = "Gain"
        elif line.startswith("* Effectiveness:"):
            section = "After"  # FUSION logs only have the results after fusion
        elif line.startswith("---"):
            section = None
        elif section:
            match = _LOG_METRIC.match(line)
            if match:
                values[section][match.group(1)] = float(match.group(2))

    if task == "FUSION":
        log_parameters.update(values["After"])
    else:
        for name, before in values["Before"].items():
            log_parameters[name] = {"Before": before,
                                    "After": values["After"].get(name),
                                    "Gain": values["Gain"].get(name)}
    return log_parameters


# Lines of the log written by UDLF (Udl::generateExecutionLog)
_LOG_TASK = re.compile(r"^Task:\s*(\w+)")
_LOG_TIME = re.compile(r"Total Time of the Algorithm Execution:\s*(\S+)\s*s")
_LOG_METRIC = re.compile(r"^(P@\d+|Recall@\d+|MAP)\s+(\S+?)%?$")


def read_ranked_lists_file_numeric(file_path, top_k=-1):
    """
    Read a numeric ranked list and return it.

    Parameters:
        file_path (str): Path to the numeric ranked list file.
        top_k (int): Ranked list size (default is -1, meaning the entire list).

    Returns:
        list: A ranked list with image numbers.
    """
    print("\n\tReading file...", file_path)
    
    with open(file_path, "r") as f:
        ranked_list = [line.strip().split(" ") for line in f]

    for i, elements in enumerate(ranked_list):
        ranked_list[i] = [int(y) for y in elements]
        if top_k != -1:
            ranked_list[i] = ranked_list[i][:top_k]

    if top_k != -1:
        print("\n\t** Returned ranked list size (limited to top_k):", len(ranked_list[0]))
    else:
        print("\n\t** Returned all the ranked list with size:", len(ranked_list[0]))
    
    return ranked_list


def read_ranked_lists_file_string(file_path, top_k=-1):
    """
    Read a numeric ranked list and return it.

    Parameters:
        file_path (str): Path to the numeric ranked list file.
        top_k (int): Ranked list size (default is -1, meaning the entire list).

    Returns:
        list: A ranked list with image numbers.
    """
    print("\n\tReading file...", file_path)
    
    with open(file_path, "r") as f:
        ranked_list = [line.strip().split(" ") for line in f]

    for i, elements in enumerate(ranked_list):
        #ranked_list[i] = [int(y) for y in elements]
        if top_k != -1:
            ranked_list[i] = ranked_list[i][:top_k]

    if top_k != -1:
        print("\n\t** Returned ranked list size (limited to top_k):", len(ranked_list[0]))
    else:
        print("\n\t** Returned all the ranked list with size:", len(ranked_list[0]))
    
    return ranked_list


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


def read_classes(lists_path="", classes_path="", input_type=None):
    '''
    Given the lists file and the classes file (UDLF format, "name:class"),
    return the class of each element, in the order of the lists file.

    Class labels are returned as int when numeric, otherwise as str.
    If input_type is given, the paths are taken from it.
    '''
    if input_type is not None:
        classes_path = str(input_type.get_classes_file()[0].strip())
        lists_path = str(input_type.get_lists_file()[0].strip())

    # like UDLF, both files are read as whitespace separated tokens
    with open(lists_path) as f:
        lists = f.read().split()

    classes_dict = dict()
    with open(classes_path) as f:
        for token in f.read().split():
            name, _, label = token.partition(':')
            classes_dict[name] = int(label) if label.lstrip('-').isdigit() else label

    missing = [element for element in lists if element not in classes_dict]
    if missing:
        raise KeyError(f"{len(missing)} elements of {lists_path} have no class in "
                       f"{classes_path} (first: {missing[0]!r})")

    return [classes_dict[element] for element in lists]
