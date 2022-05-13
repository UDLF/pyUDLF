import os
from re import X
from sre_compile import isstring
# from utils import configGenerator
from pyUDLF.utils import readData
from pyUDLF.utils import outputType
from pyUDLF.utils import gridSearch
from sys import platform
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
                udlf_urls[operating_gsystem]))

        # perform extraction
        # (lembrar que no windows é um zip)
        file = tarfile.open(compressed_binary_path)
        file.extractall(pyudlf_dir)
        file.close()
    else:
        pass
        #print("UDLF binary files found succesfully!")


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
    #print("Successful execution...")

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


def run(input_type, get_output=False):
    """
    Run with created config

    Parameters:
        input_type -> input class

    Return:
        returns an output class
    """
    global config_path, bin_path
    #verify_bin(config_path, bin_path)
    input_path = os.path.join(os.path.dirname(
        bin_path), "run_created_config.ini")
    input_type.write_config(input_path)
    output = runWithConfig(input_path, get_output)
    return output
    # config_path = inputType.get_generatedConfig()?


def find_best_method(input_type, ranked_list_size=0):
    """
    """
    global config_path, bin_path

    # setando o tamanho da ranked list de todo methodo
    if(ranked_list_size != 0):
        input_type.set_ranked_lists_size(ranked_list_size)

    # pegando todos os metodos disponiveis
    methods = input_type.get_method_name()
    methods = methods[1].split(":")
    methods = methods[0].split("(")
    methods = methods[1].split(")")
    methods = methods[0].split("|")

    # pegando os parametros
    # antes de pegar, testar se esta computando

    precision_param = input_type.get_param(
        "EFFECTIVENESS_PRECISIONS_TO_COMPUTE")
    recall_param = input_type.get_param("EFFECTIVENESS_RECALLS_TO_COMPUTE")

    precision_param = precision_param[0].strip().split(",")
    recall_param = recall_param[0].strip().split(",")

    for i in range(len(precision_param)):
        precision_param[i] = "P@"+precision_param[i].strip()
    for i in range(len(recall_param)):
        recall_param[i] = "Recall@"+recall_param[i].strip()

    # criando o dicionario
    best_dict = dict()

    # Verificando quais valores computar
    r_values = True
    p_values = True
    map_values = True

    r_values = input_type.get_param("EFFECTIVENESS_COMPUTE_RECALL")
    p_values = input_type.get_param("EFFECTIVENESS_COMPUTE_PRECISIONS")
    map_values = input_type.get_param("EFFECTIVENESS_COMPUTE_MAP")

    r_values = r_values[0].strip()
    p_values = p_values[0].strip()
    map_values = map_values[0].strip()

    # adicionando chaves com valores vazias ao dicionario
    #new_value = [(0, "TEST"), (0, "TEST")]

    # adicionar chaves de recall
    if(r_values):
        for param in recall_param:
            best_dict[param] = []

    # adicionar chaves precision
    if(p_values):
        for param in precision_param:
            best_dict[param] = []

    # adicionar chave map
    if(map_values):
        best_dict["MAP"] = []

    # salvando methodo antigo
    # corrigir pq get_method ta trazendo tudo, precisa tirar o split
    old_method = input_type.get_method_name()[0].strip()

    # iterando sobre cada methodo.
    # methodo NONE nao contabiliza

    # methodos para corrigir!!!!
    # rlsim e RDPAC

    for method in methods[1:]:
        if True:  # (method != "RDPAC") and (method != "RLSIM"):
            input_type.set_method_name(method)
            print(method)
            # se a saida for falsa, significa que o methodo n esta configurado direito, entao, colocar valores none.
            # caso contrario, funciona normalmente
            output = run(input_type, get_output=True)
            if(output == False):
                print(
                    "Error when executing the {} method, your results will not be counted!".format(method))
                if(r_values):
                    for param in recall_param:
                        best_dict[param].append(("NONE", method))
                        # pegar o recall

                        # adicionar chaves precision
                if(p_values):
                    for param in precision_param:
                        best_dict[param].append(("NONE", method))

                    # adicionar chave map
                if(map_values):
                    # print(output_values['MAP']['After'])
                    best_dict['MAP'].append(("NONE", method))
            else:
                output_values = output.get_log()
                if(r_values):
                    for param in recall_param:
                        rv = output_values[param]['After']
                        best_dict[param].append((rv, method))
                        # pegar o recall

                        # adicionar chaves precision
                if(p_values):
                    for param in precision_param:
                        pv = output_values[param]['After']
                        best_dict[param].append((pv, method))

                    # adicionar chave map
                if(map_values):
                    # print(output_values['MAP']['After'])
                    value = output_values['MAP']['After']
                    best_dict['MAP'].append((value, method))
        #best_dict['MAP'] = sorted(best_dict['MAP'], reverse=True)

    for param in best_dict:
        best_dict[param] = sorted(best_dict[param], reverse=True)

    # print(best_dict['MAP'])
    # print(best_dict['Recall@4'])
    # print(old_method)
    input_type.set_method_name(old_method)
    return best_dict

# metodo rdpac e rlsim nao estao sendo contabilizados


def find_best_param(input_type, method, param_value, list_values, ranked_list_size=0, verbose=False):
    """
    method -> metodo para testa o parametro
    param -> parametro para variar
    list_values -> lista com os valores do parametro
    """
    global config_path, bin_path

    # salvando valores antigos
    old_method = input_type.get_method_name()[0].strip()
    old_ranked_list_size = input_type.get_param(
        "PARAM_{}_L".format(method.upper()))[0].strip()

    # setar o novo metodo
    input_type.set_method_name(method)

    # setar o tamanho do ranked list do methodo apenas
    if(ranked_list_size != 0):
        input_type.set_param('PARAM_{}_L'.format(
            method.upper()), ranked_list_size)

    # criando o dicionario
    best_dict = dict()

    precision_param = input_type.get_param(
        "EFFECTIVENESS_PRECISIONS_TO_COMPUTE")
    recall_param = input_type.get_param("EFFECTIVENESS_RECALLS_TO_COMPUTE")

    precision_param = precision_param[0].strip().split(",")
    recall_param = recall_param[0].strip().split(",")

    for i in range(len(precision_param)):
        precision_param[i] = "P@"+precision_param[i].strip()
    for i in range(len(recall_param)):
        recall_param[i] = "Recall@"+recall_param[i].strip()

    # criando o dicionario
    best_dict = dict()

    # Verificando quais valores computar
    r_values = True
    p_values = True
    map_values = True

    r_values = input_type.get_param("EFFECTIVENESS_COMPUTE_RECALL")
    p_values = input_type.get_param("EFFECTIVENESS_COMPUTE_PRECISIONS")
    map_values = input_type.get_param("EFFECTIVENESS_COMPUTE_MAP")

    r_values = r_values[0].strip()
    p_values = p_values[0].strip()
    map_values = map_values[0].strip()

    # adicionar chaves de recall
    if(r_values):
        for param in recall_param:
            best_dict[param] = []

    # adicionar chaves precision
    if(p_values):
        for param in precision_param:
            best_dict[param] = []

    # adicionar chave map
    if(map_values):
        best_dict["MAP"] = []

    if verbose is True:
        print("Running for the {} method, changing the {} parameters".format(
            method, param_value))

    if isinstance(list_values, list):
        for value in list_values:
            if isinstance(value, str):
                value = value.upper()

            if verbose is True:
                print("Running to value {}".format(value))

            # alterar parametros
            input_type.set_param(param_value, value)
            # rodar
            output = run(input_type, get_output=True)
            if(output == False):
                if verbose is True:
                    print(
                        "Error when executing the {} value, your results will not be accounted for!".format(value))
                if(r_values):
                    for param in recall_param:
                        best_dict[param].append(("NONE", value))

                if(p_values):
                    for param in precision_param:
                        best_dict[param].append(("NONE", value))

                if(map_values):
                    # print(output_values['MAP']['After'])
                    best_dict['MAP'].append(('NONE', value))
            else:
                output_values = output.get_log()

                if(r_values):
                    for param in recall_param:
                        rv = output_values[param]['After']
                        best_dict[param].append((rv, value))
                        # pegar o recall

                        # adicionar chaves precision
                if(p_values):
                    for param in precision_param:
                        pv = output_values[param]['After']
                        best_dict[param].append((pv, value))

                    # adicionar chave map
                if(map_values):
                    # print(output_values['MAP']['After'])
                    mv = output_values['MAP']['After']
                    best_dict['MAP'].append((mv, value))

    # voltar o valor original
        # setar o novo metodo
    input_type.set_method_name(old_method)

    # setar o tamanho do ranked list do methodo apenas
    if(ranked_list_size != 0):
        input_type.set_param('PARAM_{}_L'.format(
            method.upper()), old_ranked_list_size)

    for param in best_dict:
        best_dict[param] = sorted(best_dict[param], reverse=True)


# ------------------------------------------------------------
    # retornar os valores originais de tudo
    # retornando metodo antigo
        # setar o novo metodo
    input_type.set_method_name(old_method)

    # setar o tamanho do ranked list do methodo apenas
    if(ranked_list_size != 0):
        input_type.set_param('PARAM_{}_L'.format(
            method.upper()), old_ranked_list_size)
    return best_dict
