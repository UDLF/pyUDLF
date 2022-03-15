
def write_data(mtx, path):
    f = open(path, "w+")
    for i in range(len(mtx)):
        for y in range(len(mtx[i])):
            f.write("{} ".format(str(mtx[i][y])))
        f.write("\n")

    f.close()
