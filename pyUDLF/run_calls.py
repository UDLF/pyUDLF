from pyUDLF.utils import readData
from pyUDLF.utils import outputType
from pyUDLF.utils import evaluation
from sys import platform
import os
import requests
import tarfile


# get paths
user_home = os.path.expanduser("~/")  # user home
# general install path (pode colocar configs tmp nele e tudo mais)
pyudlf_dir = os.path.join(user_home, ".pyudlf")
udlf_install_path = os.path.join(
    pyudlf_dir, "bin")  # path of extracted udlf file

bin_path = os.path.join(udlf_install_path, "udlf")
config_path = os.path.join(udlf_install_path, "config.ini")

# bin_path = "udlf"  # /usr/local/bin/.udlf_bin/bin/udlf - como estava antes !
# config_path = "config"
operating_system = "linuxORwindows"
compressed_binary_path = os.path.join(pyudlf_dir, "udlf_bin.tar.gz")

udlf_urls = {"linux": "http://udlf_linux.lucasvalem.com",
             "windows": "http://udlf_windows.lucasvalem.com"}

if "linux" in platform:
    operating_system = "linux"
elif platform == "win32":
    operating_system = "windows"


def setBinaryPath(path):
    """
    Set the binary path

    Parameters:
        path -> binary path
    """
    global bin_path
    bin_path = path


def setConfigPath(path):    # configPath/config.ini
    """
    Set the config path

    Parameters:
        path -> config path
    """
    global config_path      # obrigatorio por nome da config
    config_path = path
    # configGenerator.initParameters(config_path)


def getBinaryPath():
    """
    Set the binary path

    Parameters:
        path -> binary path
    """
    global bin_path
    return bin_path


def getConfigPath():
    """
    Set the binary path

    Parameters:
        path -> binary path
    """
    global config_path
    return config_path


def download_url(url, save_path, chunk_size=128):
    """
    """
    print("Downloading udlf binary...")
    r = requests.get(url, stream=True)
    # verify if got response
    if not r.ok:
        return False
    with open(save_path, 'wb') as fd:
        for chunk in r.iter_content(chunk_size=chunk_size):
            fd.write(chunk)
    print("Succesfully downloaded udlf binary!")
    return True


def verify_bin(config_path, bin_path):
    global operating_system
    global compressed_binary_path

    if (not os.path.isfile(bin_path)) or (not os.path.isfile(config_path)):
        print("UDLF binary or config is missing...")
        # create pyudlf install dir
        # (no pyudlf precisar verificar se o binário ja existe)
        if not os.path.isdir(pyudlf_dir):
            os.mkdir(pyudlf_dir)

        # download binary
        # (lembrar que no windows é um zip)
        try:
            download_success = download_url(
                udlf_urls[operating_system], compressed_binary_path)
        except Exception as e:
            print("Could not download file due to exception {}".format(e))
        if not download_success:
            print("Could not download file! Invalid url {}".format(
                udlf_urls[operating_system]))

        # perform extraction
        # (lembrar que no windows é um zip)
        file = tarfile.open(compressed_binary_path)
        file.extractall(pyudlf_dir)
        file.close()
    else:
        pass
        # print("UDLF binary files found succesfully!")


def run_platform(config_file, bin_path):
    global operating_system
    global compressed_binary_path

    if "linux" in platform:
        operating_system = "linux"
    elif platform == "win32":
        operating_system = "windows"

    verify_bin(config_file, bin_path)

    bin_path_dirname = os.path.dirname(bin_path)
    path_log_out = os.path.join(bin_path_dirname, "log_out.txt")
    cmd = "{} {} > {}".format(bin_path, config_file, path_log_out)
    if operating_system == "windows":
        cmd = "call "+cmd

    os.system(cmd)  # executa
    # return verify_running("{}/log_out.txt".format(bin_path_dirname))
    return verify_running(path_log_out)


def verify_running(path):
    """
    """
    error_vet = ["invalid", "error", "warning", "can't"]
    error_flag = False
    with open(path, 'r') as f:
        lines = [x.strip() for x in f.readlines()]
        for i in range(len(lines)):
            for j in range(len(error_vet)):
                if error_vet[j] in lines[i].lower():
                    print(lines[i])
                    error_flag = True

    return error_flag


def runWithConfig(config_file=None, get_output=False):
    """
    Run with an existing config

    Parameters:
        config_file -> config name

    Return:
        returns an output class
    """
    global bin_path, config_path
    output = outputType.OutputType()

    # if(config_file is None):
    #   config_file = config_path

    if run_platform(config_file, bin_path):
        print("Could not run")
        return False
    # print("Successful execution...")

    if (get_output is True):
        with open(config_file, 'r') as f:
            lines = [x.strip() for x in f.readlines()]
            i = 0
            flag = True
            while(flag):
                if "OUTPUT_FILE_PATH" in lines[i]:
                    line = lines[i].split('=')
                    line = line[1].split('#')
                    line = line[0].strip()
                    output.rk_path = "{}.txt".format(line)
                    output.matrix_path = "{}.txt".format(line)

                if "OUTPUT_LOG_FILE_PATH" in lines[i]:  # last
                    line = lines[i].split('=')
                    line = line[1].split('#')
                    line = line[0].strip()
                    output.log_path = line
                    flag = False

                i = i + 1

        # output.log_path = "{}/log.txt".format(os.path.dirname(bin_path))
        output.log_dict = readData.read_log(output.log_path)

    # output.rk_path = "output.txt"
    # output.matrix_path = "output.txt"

    return output


def run(input_type, get_output=False, compute_individual_gain=False, depth=-1):
    """
    Run with created config

    Parameters:
        input_type -> input class

    Return:
        returns an output class
    """

    global config_path, bin_path
    # verify_bin(config_path, bin_path)
    input_path = os.path.join(os.path.dirname(
        bin_path), "run_created_config.ini")
    input_type.write_config(input_path)
    output = runWithConfig(input_path, get_output)

    if compute_individual_gain:

        # verify output files
        validation = input_type.get_param("OUTPUT_FILE")[0].strip()
        if(not validation):
            print("WARNING!")
            print("Unable to calculate the individual gain, return was not requested, please check if the parameter 'OUTPUT_FILE' is true")
            print("Running without calculating individual gain!")
            compute_individual_gain = False

        # verify necessary conditions:
            # file format must be RK
        file_input_format = input_type.get_param(
            "INPUT_FILE_FORMAT")[0].strip()
        file_output_format = input_type.get_param(
            "OUTPUT_FILE_FORMAT")[0].strip()
        if (file_output_format != "RK"):
            print("ERROR!")
            print("Output file must be in ranked list type!")
            print("Running without calculating individual gain!")
            compute_individual_gain = False

        if (file_input_format == "MATRIX"):
            print("ERROR!")
            print("Input file must be in ranked list type!")
            print("Running without calculating individual gain!")
            compute_individual_gain = False

            # numeric rk
        rk_input_format = input_type.get_param("INPUT_RK_FORMAT")[0].strip()
        rk_output_format = input_type.get_param("OUTPUT_RK_FORMAT")[0].strip()
        if (rk_input_format != "NUM") or (rk_output_format != "NUM"):
            print("ERROR!")
            print("Input or output must be in numerical format!")
            print("Running without calculating individual gain!")
            compute_individual_gain = False

        # verify UDL taks
        task = input_type.get_param("UDL_TASK")[0].strip()
        if task != "UDL":
            print("ERROR!")
            print("Task needs to be UDL")
            print("Running without calculating individual gain!")
            compute_individual_gain = False

        if compute_individual_gain:
            before_path = input_type.get_param("INPUT_FILE")[0].strip()
            classes_list = readData.read_classes(input_type.get_lists_file()[
                                                 0].strip(), input_type.get_classes_file()[0].strip())

            rks_before = readData.read_ranked_lists_file_numeric(before_path)
            rks_after = readData.read_ranked_lists_file_numeric(output.rk_path)

            if depth == -1:
                print("Warnig!")
                print("Depth not set, using dataset size instead!")
                depth = len(rks_before)

            if len(rks_before) < depth:
                print(
                    "Warning, ranked_list size larger than the depth, set depth to max ranked list size!")
                depth = len(rks_before)

            output.individual_gain_list = evaluation.compute_gain(
                rks_before, rks_after, classes_list, depth, measure="Precision", verbose=True)

    return output
    # config_path = inputType.get_generatedConfig()?
