from pyUDLF.utils import readData
from PIL import Image
import numpy as np

# ler no config o metodo numerico ou str do rk


class OutputType:
    """
    Class to handle the outputs
    """

    def __init__(self, nome=None):
        """
        Initial class parameters.
        """
        # dictionary with log data
        self.log_dict = dict()
        self.rk_path = nome
        self.matrix_path = nome
        self.log_path = nome
        self.individual_gain_list = []
        self.images_path = nome
        self.list_path = nome

    def get_matrix(self):
        """
        Read matrix file

        Parameters:
            matrix_path -> matrix path

        Return:
            returns a matrix
        """
        if self.matrix_path is None:
            print("The shape of the output is not matrix!")
            return None

        matrix = readData.read_matrix_file(self.matrix_path)
        return matrix

    def get_rks(self, top_k=1000):
        """
        Read string ou numeric ranked list

        Parameters:
            rk_patk -> ranked list path

        Return:
            returns a ranked list with image numbers or names
        """
        if self.rk_path is None:
            print("The shape of the output is not RK!")
            return None

        rks = readData.read_ranked_lists_file_string(self.rk_path, top_k=top_k)
        try:
            rks = [[int(elem) for elem in rk] for rk in rks]
        finally:
            return rks

    def get_log(self):
        """
        Returns the result of the execution !
        """
        if self.log_path is None:
            print("Output was not requested at execution! Log does not exist!")
            return None

        self.log_dict = readData.read_log(self.log_path)
        # for param in self.log_dict:
        #    print("{} = {}".format(param, self.log_dict[param])) return ou nao?

        return self.log_dict
        # original n tinha nada

    def get_individual_gain_list(self):
        # print(self.get_individual_gain_list)
        return self.individual_gain_list

    def print_log(self, log_value=None):
        """
        Display log
        """
        if self.log_path is None:
            print("Output was not requested at execution! Log does not exist!")
            return None

        if log_value is None:
            for param in self.log_dict:
                print("{:<10} = {}".format(param, self.log_dict[param]))
        else:
            if isinstance(log_value, dict):
                for param in log_value:
                    print("{:<10} = {}".format(param, log_value[param]))

    def show_rk(self, line, vis_rk_size=10):

        if self.images_path is None:
            print("Unable to generate preview, image path is empty!")
            return

        f = open(self.rk_path)
        all_lines = f.readlines()
        f.close()

        f = open(self.list_path)
        list_test = [x.replace('\n', '') for x in f.readlines()]
        f.close()
        # print(list_test)

        only_one = all_lines[line].split()
        # print(only_one)

        images_show_list = []
        for i in range(vis_rk_size):
            # print(only_one[i])
            images_show_list.append(
                self.images_path + list_test[int(only_one[i])])

        imgs = [Image.open(i) for i in images_show_list]

        # pick the image which is the smallest, and resize the others to match it (can be arbitrary image shape here)
        min_shape = sorted([(np.sum(i.size), i.size) for i in imgs])[0][1]
        imgs_comb = np.concatenate(
            [np.array(x.resize(min_shape)) for x in imgs], axis=1)

        # save that beautiful picture
        imgs_comb = Image.fromarray(imgs_comb)
        imgs_comb.show()
