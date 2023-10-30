import numpy as np


def compute_map(rks, classes_list, map_depth=-1):
    map_list = []
    class_size_dict = get_class_size_dict(classes_list)
    
    if map_depth == -1:
        print("WARNING: depth of the ranked_list size not set, setting to max ranked list size!")
        map_depth = len(rks)


    if len(rks) <= map_depth:
        if len(rks) < map_depth:
            print(
                "WARNING: depth larger than the ranked_list size, set depth to max ranked list size!")
        map_depth = len(rks)
        # print(map_depth)

    for i, rk in enumerate(rks):
        acum = 0
        value = 0
        # print(rk)
        # cl_i = class_size_dict[i]#i//class_size
        cl_i = classes_list[i]
        # if len(rks)<=depth
        # else colocar tamanho maximo q eh len(rks)dar um warnin

        for j in range(map_depth):
            cl_j = classes_list[rk[j]]
            if cl_i == cl_j:
                value += 1
                acum += value/(j+1)

        map_list.append(acum/class_size_dict[cl_i])
        # map_list.append(acum/class_size_dict[cl_i]) ###
    map_value = np.mean(map_list)
    return round(map_value, 4), map_list


def get_class_size_dict(class_list):
    class_size_dict = dict()
    for i in range(len(class_list)):
        if class_list[i] not in class_size_dict:
            class_size_dict[class_list[i]] = 1
        else:
            class_size_dict[class_list[i]] = class_size_dict[class_list[i]] + 1

    return class_size_dict


def compute_recall(rks, classes_list, r_depth=-1):
    recall_list = []
    class_size_dict = get_class_size_dict(classes_list)
    
    if r_depth == -1:
        print("WARNING: depth of the ranked_list size not set, setting to max ranked list size!")
        r = len(rks)
        
    if len(rks) <= r_depth:
        if len(rks) < r_depth:
            print(
                "Warning, depth larger than the ranked_list size, set depth to max ranked list size!")
        r_depth = len(rks)

    for i, rk in enumerate(rks):
        acum = 0
        # print(rk)
        cl_i = classes_list[i]
        for j in range(r_depth):
            cl_j = classes_list[rk[j]]
            if cl_i == cl_j:
                acum += 1

        recall_list.append(acum/class_size_dict[cl_i])
        # map_list.append(acum/class_size_dict[cl_i]) ###
    r_value = np.mean(recall_list)
    return round(r_value, 4), recall_list


def compute_precision(rks, classes_list, p_depth=-1):
    precision_list = []
    class_size_dict = get_class_size_dict(classes_list)
    if p_depth == -1:
        print("WARNING: depth of the ranked_list size not set, setting to max ranked list size!")
        p_depth = len(rks)
        
    if len(rks) <= p_depth:
        if len(rks) < p_depth:
            print(
                "Warning, depth larger than the ranked_list size, set depth to max ranked list size!")
        p_depth = len(rks)

    for i, rk in enumerate(rks):
        acum = 0
        # print(rk)
        cl_i = classes_list[i]
        for j in range(p_depth):
            cl_j = classes_list[rk[j]]
            if cl_i == cl_j:
                acum += 1

        precision_list.append(acum/p_depth)
        # map_list.append(acum/class_size_dict[cl_i]) ###
    p_value = np.mean(precision_list)
    return round(p_value, 4), precision_list


def compute_gain(before_rks, after_rks, classes_list, depth=-1, measure="MAP", verbose=True):
    
    if depth == -1:
        print("WARNING: depth of the ranked_list size not set, setting to max ranked list size!")
        depth = len(before_rks)
    
    measure = measure.upper()
    if verbose:
        print()
        print("Calculating the gain for {} with depth {}".format(measure, depth))

    before_mean = 0
    after_mean = 0
    before_list = []
    after_list = []
    gain_list = []
    class_size_dict = get_class_size_dict(classes_list)

    if measure == "MAP":
        before_mean, before_list = compute_map(before_rks, classes_list, depth)
        after_mean, after_list = compute_map(after_rks, classes_list, depth)
    elif measure == "PRECISION":
        before_mean, before_list = compute_precision(
            before_rks, classes_list, depth)
        after_mean, after_list = compute_precision(
            after_rks, classes_list, depth)
    elif measure == "RECALL":
        before_mean, before_list = compute_recall(
            before_rks, classes_list, depth)
        after_mean, after_list = compute_recall(after_rks, classes_list, depth)

    #gain_mean = round(after_mean - before_mean, 4)
    # print("aqui")
    #print(before_mean, after_mean)
    #gain_mean_percent = round((((after_mean-before_mean))/before_mean)*100, 4)
    #gain_mean_percent = (((after_mean-before_mean))/before_mean)*100
    # print(gain_mean_percent)

    for i in range(len(after_list)):
        gain_list.append((round(after_list[i]-before_list[i], 4), i))

    return gain_list  # , gain_mean_percent, gain_mean
