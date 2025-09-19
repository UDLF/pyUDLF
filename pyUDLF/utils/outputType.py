import os
from pathlib import Path
from typing import Optional, List, Union

import numpy as np
from PIL import Image, ImageDraw

from pyUDLF.utils import readData
from pyUDLF.utils.logger import get_logger

logger = get_logger(__name__)

class OutputType:
    """
    Handle outputs produced by UDLF (matrix, ranked lists, logs, visualizations).
    """

    def __init__(self, path: Optional[str] = None) -> None:
        """
        Initialize OutputType with optional base path.
        
        Args:
            path (str, optional): Base path for outputs (rk, matrix, log, etc.).
        """
        self.log_dict: dict = {}
        self.rk_path: Optional[str] = path
        self.matrix_path: Optional[str] = path
        self.log_path: Optional[str] = path
        self.individual_gain_list: list = []
        self.images_path: Optional[str] = path
        self.list_path: Optional[str] = path
        self.classes_path: Optional[str] = path

        logger.debug("OutputType initialized with base path: %r", path)

    def get_matrix(self) -> List[List[float]]:
        """
        Read the matrix output file and return it as a list of lists.

        Returns:
            List[List[float]]: matrix of floats.

        Raises:
            FileNotFoundError: if matrix_path is not set or file does not exist.
            ValueError: if the file contents cannot be parsed as floats.
        """
        if not self.matrix_path:
            logger.error("Matrix path not set. The output is not a matrix.")
            raise FileNotFoundError("Matrix path not set.")

        p = Path(self.matrix_path)
        if not p.is_file():
            logger.error("Matrix file not found: %s", self.matrix_path)
            raise FileNotFoundError(f"Matrix file not found: {self.matrix_path}")

        try:
            matrix = readData.read_matrix_file(self.matrix_path)
            logger.debug(
                "Matrix read from %s (shape: %dx%d)",
                self.matrix_path,
                len(matrix),
                len(matrix[0]) if matrix else 0,
            )
            return matrix
        except Exception as e:
            logger.exception("Failed to read matrix file %s: %s", self.matrix_path, e)
            raise ValueError(f"Failed to parse matrix file {self.matrix_path}: {e}")

    def get_rks(
        self, top_k: int = 1000, expect_numeric: Optional[bool] = None
    ) -> List[List[Union[int, str]]]:
        """
        Read ranked lists (RK) from file.

        Args:
            top_k (int): Limit each ranked list to the top-k elements. Default=1000.
            expect_numeric (Optional[bool]):
                - True: force conversion to int (raise error if fails).
                - False: keep strings.
                - None: try to convert, fallback to strings.

        Returns:
            List[List[int]] if numeric, or List[List[str]] if string.

        Raises:
            FileNotFoundError: if rk_path is not set or file does not exist.
            ValueError: if forced numeric conversion fails.
        """
        if not self.rk_path:
            logger.error("RK path not set. The output is not RK.")
            raise FileNotFoundError("RK path not set.")

        p = Path(self.rk_path)
        if not p.is_file():
            logger.error("Ranked list file not found: %s", self.rk_path)
            raise FileNotFoundError(f"Ranked list file not found: {self.rk_path}")

        try:
            rks = readData.read_ranked_lists_file_string(self.rk_path, top_k=top_k)
        except Exception as e:
            logger.exception("Failed to read ranked list file %s: %s", self.rk_path, e)
            raise ValueError(f"Failed to read ranked list file {self.rk_path}: {e}")

        # force numeric
        if expect_numeric is True:
            try:
                return [[int(elem) for elem in rk] for rk in rks]
            except Exception as e:
                logger.exception("Forced numeric conversion failed: %s", e)
                raise ValueError(
                    f"Numeric conversion failed for ranked list file {self.rk_path}: {e}"
                )

        # force string
        if expect_numeric is False:
            return rks

        # auto-detect (try convert, fallback)
        try:
            return [[int(elem) for elem in rk] for rk in rks]
        except Exception:
            logger.debug("Ranked lists contain non-numeric entries; returning as strings.")
            return rks


    def get_log(self) -> dict:
        """
        Get the execution log dictionary.

        Returns:
            dict: execution log with metrics and parameters.

        Raises:
            FileNotFoundError: if log_path is not set or file does not exist.
        """
        if not self.log_path:
            logger.error("Log path not set. Output was not requested at execution.")
            raise FileNotFoundError("Log path not set. Output does not exist.")

        p = Path(self.log_path)
        if not p.is_file():
            logger.error("Log file not found: %s", self.log_path)
            raise FileNotFoundError(f"Log file not found: {self.log_path}")

        if not self.log_dict:
            try:
                self.log_dict = readData.read_log(self.log_path)
                logger.debug("Log loaded successfully from %s", self.log_path)
            except Exception as e:
                logger.exception("Failed to read log file %s: %s", self.log_path, e)
                raise ValueError(f"Failed to read log file {self.log_path}: {e}")

        return self.log_dict

    def get_individual_gain_list(self) -> list:
        """
        Get the individual gain list.

        Returns:
            list: gain values for each individual element.
        """
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
