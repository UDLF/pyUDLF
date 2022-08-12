from pyUDLF.utils import readData
from pyUDLF.utils import outputType
from pyUDLF.utils import evaluation
from sys import platform
import os
import requests
import tarfile

config_path = None
bin_path = None
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
    return verify_running(path_log_out), path_log_out


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


def individual_gain_config_running(config_file=None, depth=-1):
    individual_gain_list = []

    task = ""
    in_file_format = ""
    in_rk_format = ""
    out_file = ""
    out_file_format = ""
    out_rk_format = ""
    before_path = ""
    list_path = ""
    classes_path = ""
    after_path = ""

    with open(config_file, 'r') as f:
        lines = [x.strip() for x in f.readlines()]
        i = 0
        flag = True
        while(flag):
            if "UDL_TASK" in lines[i]:
                line = lines[i].split('=')
                line = line[1].split('#')
                line = line[0].strip()
                task = line

            if "INPUT_FILE" in lines[i]:
                if lines[i].split('=')[0].strip() == "INPUT_FILE":
                    line = lines[i].split('=')
                    line = line[1].split('#')
                    line = line[0].strip()
                    before_path = line

            if "INPUT_FILE_LIST" in lines[i]:
                line = lines[i].split('=')
                line = line[1].split('#')
                line = line[0].strip()
                list_path = line

            if "INPUT_FILE_CLASSES" in lines[i]:
                line = lines[i].split('=')
                line = line[1].split('#')
                line = line[0].strip()
                classes_path = line

            if "INPUT_FILE_FORMAT" in lines[i]:
                line = lines[i].split('=')
                line = line[1].split('#')
                line = line[0].strip()
                in_file_format = line

            if "INPUT_RK_FORMAT" in lines[i]:
                line = lines[i].split('=')
                line = line[1].split('#')
                line = line[0].strip()
                in_rk_format = line

            if "OUTPUT_FILE" in lines[i]:
                # print(lines[i].split('=')[0])
                if lines[i].split('=')[0].strip() == "OUTPUT_FILE":
                    # print(lines[i])
                    line = lines[i].split('=')
                    line = line[1].split('#')
                    line = line[0].strip()
                    out_file = line

            if "OUTPUT_FILE_FORMAT" in lines[i]:
                line = lines[i].split('=')
                line = line[1].split('#')
                line = line[0].strip()
                out_file_format = line

            if "OUTPUT_RK_FORMAT" in lines[i]:
                line = lines[i].split('=')
                line = line[1].split('#')
                line = line[0].strip()
                out_rk_format = line

            if "OUTPUT_FILE_PATH" in lines[i]:  # last
                line = lines[i].split('=')
                line = line[1].split('#')
                line = line[0].strip()
                after_path = "{}.txt".format(line)
                flag = False

            i = i + 1

        # verifications
    if task != "UDL":
        print("ERROR!")
        print("Task needs to be UDL")
        print("Running without calculating individual gain!")
        return None

    if(out_file != "TRUE"):
        print("WARNING!")
        print("Unable to calculate the individual gain, return was not requested, please check if the parameter 'OUTPUT_FILE' is true")
        print("Running without calculating individual gain!")

    if (in_file_format == "MATRIX"):
        print("ERROR!")
        print("Input file must be in ranked list type!")
        print("Running without calculating individual gain!")
        return None

    if (in_file_format == "AUTO"):
        print("WARNING!")
        print("Input file must be in ranked list type! This is set to AUTO!!!!")

    if (in_rk_format != "NUM") or (out_rk_format != "NUM"):
        print("ERROR!")
        print("Input or output must be in numerical format!")
        print("Running without calculating individual gain!")
        return None

    if (out_file_format != "RK"):
        print("ERROR!")
        print("Output file must be in ranked list type!")
        print("Running without calculating individual gain!")
        return None

    classes_list = readData.read_classes(list_path, classes_path)
    # print(classes_list)
    rks_before = readData.read_ranked_lists_file_numeric(before_path)
    rks_after = readData.read_ranked_lists_file_numeric(after_path)

    if depth == -1:
        print("Warnig!")
        print("Depth not set, using dataset size instead!")
        depth = len(rks_before)

    if len(rks_before) < depth:
        print("Warning, depth larger than the ranked_list size, set depth to max ranked list size!")
        depth = len(rks_before)

    individual_gain_list = evaluation.compute_gain(
        rks_before, rks_after, classes_list, depth, measure="MAP", verbose=True)

    # print(individual_gain_list)
    # print(task)
    # print(in_file_format)
    # print(in_rk_format)
    # print(out_file)
    # print(out_file_format)
    # print(out_rk_format)
    # print(list_path)
    # print(classes_path)
    # print(before_path)
    # print(after_path)
    # print(depth)

    return individual_gain_list


def runWithConfig(config_file=None, get_output=False, compute_individual_gain=False, depth=-1, visualization=False):
    """
    Run with an existing config

    Parameters:
        config_file -> config name

    Return:
        returns an output class
    """
    global bin_path, config_path
    output = outputType.OutputType()
    out_rk_format = ""
    out_format = ""
    img_path = ""
    list_path = ""
    classes_path = ""

    if not os.path.isfile(config_path):
        print("Config is missing! Unable to run!")
        return
    if not os.path.isfile(bin_path):
        print("Binary is missing! Unable to run!")
        return

    # if(config_file is None):
    #   config_file = config_path
    run_verify, log_out_path = run_platform(config_file, bin_path)
    #print(run_verify, log_out_path)

    if run_verify:
        print("Could not run")
        return False
    # print("Successful execution...")

    if (get_output is True):
        with open(config_file, 'r') as f:
            lines = [x.strip() for x in f.readlines()]
            i = 0
            flag = True
            while(flag):
                if "INPUT_FILE_LIST" in lines[i]:
                    line = lines[i].split('=')
                    line = line[1].split('#')
                    line = line[0].strip()
                    list_path = line

                if "INPUT_FILE_CLASSES" in lines[i]:
                    line = lines[i].split('=')
                    line = line[1].split('#')
                    line = line[0].strip()
                    classes_path = line

                if "INPUT_IMAGES_PATH" in lines[i]:
                    line = lines[i].split('=')
                    line = line[1].split('#')
                    line = line[0].strip()
                    img_path = line
                    # print(out_format)

                if "OUTPUT_FILE_FORMAT" in lines[i]:
                    line = lines[i].split('=')
                    line = line[1].split('#')
                    line = line[0].strip()
                    out_format = line
                    # print(out_format)

                if "OUTPUT_RK_FORMAT" in lines[i]:
                    line = lines[i].split('=')
                    line = line[1].split('#')
                    line = line[0].strip()
                    out_rk_format = line
                    # print(rk_format)

                if "OUTPUT_FILE_PATH" in lines[i]:
                    line = lines[i].split('=')
                    line = line[1].split('#')
                    line = line[0].strip()
                    if(out_format == "RK"):
                        output.rk_path = "{}.txt".format(line)
                    elif(out_format == "MATRIX"):
                        output.matrix_path = "{}.txt".format(line)

                if "OUTPUT_LOG_FILE_PATH" in lines[i]:  # last
                    line = lines[i].split('=')
                    line = line[1].split('#')
                    line = line[0].strip()
                    output.log_path = line
                    flag = False

                i = i + 1

        # output.log_path = "{}/log.txt".format(os.path.dirname(bin_path))
        # esta lendo o log_out_path, q eh o log q mandei salvar junto com o binario
        output.log_dict = readData.read_log(log_out_path)
        # apagando o log_out para n ficar la. se usuario n setar o path ele salva em lugar x.
        os.remove(log_out_path)

    if (compute_individual_gain):
        output.individual_gain_list = individual_gain_config_running(
            config_file, depth)

    if (visualization):
        if(get_output):
            if(out_format == "RK"):
                if(out_rk_format == "NUM"):
                    if(os.path.isdir(img_path)):
                        output.images_path = img_path
                        output.list_path = list_path
                        output.classes_path = classes_path
                    else:
                        print("Images directory does not exist!")
                    # verificar se arquivo ou diretorio existe
                else:
                    print("The output format of the ranked lists must be 'NUM'!")
            else:
                print("The output file must be of type 'RK'!")
        else:
            print("It is necessary to request the output result!")

    # output.rk_path = "output.txt"
    # output.matrix_path = "output.txt"
    return output


def run(input_type, get_output=False, compute_individual_gain=False, depth=-1, visualization=False):
    """
    Run with created config

    Parameters:
        input_type -> input class

    Return:
        returns an output class
    """
    if not os.path.isfile(input_type.config_path):
        print("Unable to run, input_type was not initialized correctly!")
        return

    global config_path, bin_path
    # verify_bin(config_path, bin_path)
    input_path = os.path.join(os.path.dirname(
        bin_path), "run_created_config.ini")
    input_type.write_config(input_path)
    output = runWithConfig(input_path, get_output,
                           compute_individual_gain, depth, visualization)
    # se quiser ver o config, apenas comentar a linha de baixo, pois, o run escreve o config, roda o runwithconfig e apaga depois!
    os.remove(input_path)

    return output
    # config_path = inputType.get_generatedConfig()?
