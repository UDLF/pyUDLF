from turtle import shape
from pyUDLF.utils import readData
from PIL import Image, ImageDraw
import numpy as np
import os

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
        self.classes_path = nome

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

        #self.log_dict = readData.read_log(self.log_path)
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

    def show_rk(self, line, rk_size=10, images_shape=(0, 0), start_element=0):
        return self.__internal_rk_images_use__(line, rk_size, images_shape=images_shape, start_element=start_element)

    def save_rk_img(self, line, rk_size=10, images_shape=(0, 0), img_path="", start_element=0):
        if not isinstance(img_path, str):
            print("ERROR! Path must be of type string")
            return

        return self.__internal_rk_images_use__(line, rk_size, images_shape=images_shape, save=True, img_path=img_path, start_element=start_element)

    def __internal_rk_images_use__(self, line, rk_size=10, images_shape=(0, 0), save=False, img_path="", start_element=0):
        min_shape = (0, 0)

        #################
        if ((self.list_path is None) or (self.classes_path is None) or (self.images_path is None)):
            print("Something is wrong. Unable to generate preview!")
            return
        ###############
        classes_list = readData.read_classes(
            self.list_path, self.classes_path)
        # print(classes_list)

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

        # rk line for show
        only_one = all_lines[line].split()
        # print(only_one)
        # print(classes_list[int(only_one[1])])
        # taking images class
        images_class_list = []
        images_show_list = []

        # taking first element
        images_class_list.append(classes_list[int(only_one[0])])
        # print(only_one[i])
        images_show_list.append(
            self.images_path + list_test[int(only_one[0])])
        if not os.path.isfile(images_show_list[0]):
            print("No such file or directory: "+images_show_list[0])
            return

        for i in range(1, rk_size):
            j = i
            i += start_element

            # taking images class
            images_class_list.append(classes_list[int(only_one[i])])
            # print(only_one[i])
            images_show_list.append(
                self.images_path + list_test[int(only_one[i])])
            if not os.path.isfile(images_show_list[j]):
                print("No such file or directory: "+images_show_list[j])
                return

        imgs = [Image.open(i).convert('RGB') for i in images_show_list]
        # print(images_class_list)
        ##########################
        ImageDraw.Draw(imgs[0]).rectangle(
            [(0, 0), (imgs[0].width, imgs[0].height)], outline="blue", width=10)
        for i in range(1, len(imgs)):
            img = imgs[i]
            if images_class_list[0] != images_class_list[i]:
                ImageDraw.Draw(img).rectangle(
                    [(0, 0), (img.width, img.height)], outline="red", width=10)
            else:
                ImageDraw.Draw(img).rectangle(
                    [(0, 0), (img.width, img.height)], outline="green", width=10)
        # test = [ImageDraw.Draw(img).rectangle(
        #    [(0, 0), (img.width, img.height)], outline="red", width=4) for img in imgs]

        #########################

        # pick the image which is the smallest, and resize the others to match it (can be arbitrary image shape here)
        if all((
                isinstance(images_shape, tuple),
                len(images_shape) == 2,
                isinstance(images_shape[0], int),
                isinstance(images_shape[1], int))):
            if (images_shape[0] == 0 and images_shape[1] == 0):
                min_shape = sorted([(np.sum(i.size), i.size)
                                    for i in imgs])[0][1]
            else:
                min_shape = images_shape
        else:
            print("Impossible to generate visualization.")
            print("Image sizes must be a tuple of 2 elements of type integer.")
            return

        imgs_comb = np.concatenate(
            [np.array(x.resize(min_shape)) for x in imgs], axis=1)

        # save that beautiful picture
        imgs_comb = Image.fromarray(imgs_comb)

        if save:
            imgs_comb.save(img_path)
            return
        else:
            imgs_comb.show()
            return imgs_comb
