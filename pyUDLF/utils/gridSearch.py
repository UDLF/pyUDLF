from pyUDLF import run_calls


def find_best_param(input_type, method, param_value, list_values, ranked_list_size=0, verbose=False):
    """
    method -> metodo para testa o parametro
    param -> parametro para variar
    list_values -> lista com os valores do parametro
    """
    global config_path, bin_path
    type_list_values = ""

    # verificando validade dos valores
    if param_value in input_type.list_parameters:
        if "PARAM_{}".format(method) in param_value:
            # eh um parametro do metodo
            # print(isinstance(list_values[0], int))
            aux = input_type.get_param(param_value)
            aux = aux[1].split(":")[0]
            if len(aux) < 8:
                if "int" in aux:
                    type_list_values = "int"
                elif "float" in aux:
                    type_list_values = "float"
            else:
                type_list_values = "string"

            if type_list_values != "string":
                if type_list_values == "int":
                    for param in list_values:
                        if type(param) is not int:
                            print("The parameter {} accepts only integer values".format(
                                param_value))
                            print(
                                "The value {} is not an integer. Execution interrupted!".format(param))
                            return None
                else:
                    for param in list_values:
                        if type(param) is not float:
                            print("The parameter {} accepts only float values".format(
                                param_value))
                            print(
                                "The value {} is not a float. Execution interrupted!".format(param))
                            return None
            else:
                for value in list_values:
                    if value not in aux:
                        print("The value {} does not belong to the list of possible values for the parameter {}".format(
                            value, param_value))
                        print("Execution interrupted!")
                        return None

        else:
            print("Parameter does not belong to the method. Execution interrupted!")
            return None
    else:
        print("Parameter does not exist. Unable to execute!")
        return None

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
            output = run_calls.run(input_type, get_output=True)
            if(output is False):
                if verbose is True:
                    print(
                        "Error when executing the {} value, your results will not be considered for!".format(value))
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
                        best_dict[param].append((float(rv), value))
                        # pegar o recall

                        # adicionar chaves precision
                if(p_values):
                    for param in precision_param:
                        pv = output_values[param]['After']
                        best_dict[param].append((float(pv), value))

                    # adicionar chave map
                if(map_values):
                    # print(output_values['MAP']['After'])
                    mv = output_values['MAP']['After']
                    best_dict['MAP'].append((float(mv), value))

    # voltar o valor original
        # setar o novo metodo
    input_type.set_method_name(old_method)

    # setar o tamanho do ranked list do methodo apenas
    if(ranked_list_size != 0):
        input_type.set_param('PARAM_{}_L'.format(
            method.upper()), old_ranked_list_size)

    for param in best_dict:
        best_dict[param] = sorted(best_dict[param], reverse=True)
        # sorted(l, key=lambda x: 0 if x[0] is None else x[0])


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


def find_best_method(input_type, ranked_list_size=0, verbose=True):
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
    # new_value = [(0, "TEST"), (0, "TEST")]

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
            if verbose:
                print(method)
            # se a saida for falsa, significa que o methodo n esta configurado direito
            # , entao, colocar valores none.
            # caso contrario, funciona normalmente
            output = run_calls.run(input_type, get_output=True)
            if(output is False):
                print(
                    "Error when executing the {} method, your results will not be considered!".format(method))
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
        # best_dict['MAP'] = sorted(best_dict['MAP'], reverse=True)

    for param in best_dict:
        best_dict[param] = sorted(best_dict[param], reverse=True)

    # print(best_dict['MAP'])
    # print(best_dict['Recall@4'])
    # print(old_method)
    input_type.set_method_name(old_method)
    return best_dict

# metodo rdpac e rlsim nao estao sendo contabilizados


def find_best_method_with_best_k(input_type, measures=[], k_interval=[], ranked_list_size=0, verbose=True):
    # input -> intervalo do k, metricas(map, precision -> list), input_type, tamanho do ranked_list

    best_dict = dict()
    best_dict_aux = dict()

    old_k_dict = dict()

    # taking measures
    measures_list = []
    precision_param = input_type.get_param(
        "EFFECTIVENESS_PRECISIONS_TO_COMPUTE")
    recall_param = input_type.get_param("EFFECTIVENESS_RECALLS_TO_COMPUTE")

    precision_param = precision_param[0].strip().split(",")
    recall_param = recall_param[0].strip().split(",")

    for i in range(len(precision_param)):
        precision_param[i] = "P@"+precision_param[i].strip()
    for i in range(len(recall_param)):
        recall_param[i] = "Recall@"+recall_param[i].strip()

    for i in range(len(precision_param)):
        measures_list.append(precision_param[i])
    for i in range(len(recall_param)):
        measures_list.append(recall_param[i])
    measures_list.append("MAP")

    # verifying if k is int
    for param in k_interval:
        if type(param) is not int:
            print("ERROR!")
            print("The parameter k accepts only integer values!")
            print("The value {} is not an integer!".format(param))
            return None

    available_methods = input_type.get_param("UDL_METHOD")[1].strip()
    available_methods = available_methods.split(":")[0].strip("(").strip(")")
    available_methods = available_methods.split("|")

    # saving old k values:
    for methods in available_methods[1:]:
        if methods == "RLSIM":
            aux = input_type.get_param("PARAM_RLSIM_TOPK")
            if aux is not None:
                old_k_dict[methods] = aux[0].strip()
        elif methods == "RDPAC":
            aux = input_type.get_param("PARAM_RDPAC_K_END".format(methods))
            if aux is not None:
                old_k_dict[methods] = aux[0].strip()
        else:
            aux = input_type.get_param("PARAM_{}_K".format(methods))
            if aux is not None:
                old_k_dict[methods] = aux[0].strip()

    # print(old_k_dict)

    for measure in measures:
        if measure in measures_list:
            best_dict[measure] = []
            # measure = map, p@4,....
            for k in k_interval:
                if verbose:
                    print()
                    print(
                        "Running for the measure {} with the value of k {}:".format(measure, k))
                    print()
                for method in available_methods[1:]:
                    if method == "RLSIM":
                        input_type.set_param("PARAM_RLSIM_TOPK", k)
                    elif method == "RDPAC":
                        input_type.set_param("PARAM_RDPAC_K_END", k)
                    else:
                        input_type.set_param("PARAM_{}_K".format(method), k)

                best_dict_aux = find_best_method(
                    input_type, ranked_list_size=280, verbose=verbose)

                # taking best values:
                # if measure exist
                if measure in best_dict_aux:
                    # taking best available value
                    cont = 0
                    best = best_dict_aux[measure][cont]
                    while (best[0] == "NONE"):
                        cont += 1
                        best = best_dict_aux[measure][cont]

                    # To see all the values
                    # print(measure)
                    # print(best_dict_aux[measure])
                    # print("\/")
                    # print(best)
            # taking the best available parameter:
                # best_dict[measure].append((best[0], best[1], k))
                best_dict[measure].append((best[0], best[1], k))
        else:
            print()
            print(" WARNING ! ")
            print("Measure {} does not exist, it will not be counted!".format(measure))
            print()

    # fazer
    # atribuir valor antigo de volta nos metodos
    # atribuindo valores antigos de volta
    for method in available_methods[1:]:
        if method == "RLSIM":
            input_type.set_param("PARAM_RLSIM_TOPK", old_k_dict[method])
        elif method == "RDPAC":
            input_type.set_param("PARAM_RDPAC_K_END", old_k_dict[method])
        else:
            input_type.set_param("PARAM_{}_K".format(
                method), old_k_dict[method])

    # print(best_dict)
    return best_dict
