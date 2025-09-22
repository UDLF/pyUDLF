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

    def show_rk(self, line: int, rk_size: int = 10,
                images_shape: tuple[int, int] = (0, 0), start_element: int = 0):
        """
        Show a ranked list as concatenated images.

        Args:
            line (int): line index in the ranked list file (query index).
            rk_size (int): number of retrieved elements to show.
            images_shape (tuple[int, int]): resize shape (w,h). If (0,0), use smallest image.
            start_element (int): starting index offset for the ranked list.

        Returns:
            PIL.Image.Image: the combined image for visualization.

        Raises:
            ValueError: if line is not a valid index.
        """
        if type(line) is not int or line < 0:
            raise ValueError(f"line must be a non-negative integer, got {line!r}")

        # Validate range inside _render_rk_images
        return self._render_rk_images(
            line, rk_size, images_shape=images_shape, save=False,
            img_path="", start_element=start_element
        )

    def save_rk_img(self, line: int, rk_size: int = 10,
                    images_shape: tuple[int, int] = (0, 0),
                    img_path: str = "", start_element: int = 0):
        """
        Save a ranked list as concatenated images.

        Args:
            line (int): line index in the ranked list file (query index).
            rk_size (int): number of retrieved elements to save.
            images_shape (tuple[int, int]): resize shape (w,h). If (0,0), use smallest image.
            img_path (str): path to save the output image.
            start_element (int): starting index offset for the ranked list.

        Returns:
            Path: path to the saved image.

        Raises:
            ValueError: if line is not a valid index or img_path is invalid.
        """
        if not isinstance(line, int) or line < 0:
            raise ValueError(f"line must be a non-negative integer, got {line!r}")
        if not isinstance(img_path, str) or not img_path.strip():
            raise ValueError("img_path must be a non-empty string.")

        return self._render_rk_images(
            line, rk_size, images_shape=images_shape,
            save=True, img_path=img_path, start_element=start_element
        )


    # def _render_rk_images(self, line: int, rk_size: int = 10,
    #                       images_shape: tuple[int, int] = (0, 0),
    #                       save: bool = False, img_path: str = "",
    #                       start_element: int = 0):
    #     """
    #     Internal method to render ranked list images.

    #     Adds blue border to query, green to correct matches,
    #     and red to incorrect ones.

    #     Returns:
    #         PIL.Image.Image or Path: combined image, or saved path.
    #     """
    #     # Sanity check: paths must be defined
    #     if not all((self.list_path, self.classes_path, self.images_path, self.rk_path)):
    #         raise RuntimeError("Missing required paths. Cannot render ranked list.")

    #     # Load classes
    #     classes_list = readData.read_classes(self.list_path, self.classes_path)

    #     # Load ranked lists (strings)
    #     with open(self.rk_path, "r") as f:
    #         all_lines = f.readlines()

    #     if line >= len(all_lines):
    #         raise ValueError(f"line index {line} out of range (0 - {len(all_lines)-1})")

    #     # Load file list (image names)
    #     with open(self.list_path, "r") as f:
    #         list_test = [x.strip() for x in f.readlines()]

    #     # Extract ranked list for the query line
    #     only_one = all_lines[line].split()

    #     # Build image paths and corresponding classes
    #     images_class_list = []
    #     images_show_list = []

    #     # Add query (first element)
    #     query_idx = int(only_one[0])
    #     images_class_list.append(classes_list[query_idx])
    #     images_show_list.append(str(Path(self.images_path) / list_test[query_idx]))

    #     # Add retrieved results
    #     for i in range(1, rk_size):
    #         idx = int(only_one[i + start_element])
    #         images_class_list.append(classes_list[idx])
    #         images_show_list.append(str(Path(self.images_path) / list_test[idx]))

    #     # Check file existence
    #     for p in images_show_list:
    #         if not Path(p).is_file():
    #             raise FileNotFoundError(f"No such file: {p}")

    #     # Open all images
    #     imgs = [Image.open(p).convert("RGB") for p in images_show_list]

    #     # Draw borders: blue for query, green/red for results
    #     ImageDraw.Draw(imgs[0]).rectangle(
    #         [(0, 0), (imgs[0].width, imgs[0].height)], outline="blue", width=10
    #     )
    #     for i in range(1, len(imgs)):
    #         color = "green" if images_class_list[0] == images_class_list[i] else "red"
    #         ImageDraw.Draw(imgs[i]).rectangle(
    #             [(0, 0), (imgs[i].width, imgs[i].height)], outline=color, width=10
    #         )

    #     # Decide resize shape
    #     if (
    #         isinstance(images_shape, tuple)
    #         and len(images_shape) == 2
    #         and all(isinstance(x, int) for x in images_shape)
    #     ):
    #         if images_shape == (0, 0):
    #             min_shape = sorted([(np.sum(i.size), i.size) for i in imgs])[0][1]
    #         else:
    #             min_shape = images_shape
    #     else:
    #         raise ValueError("images_shape must be (int, int), e.g., (128, 128).")

    #     # Resize and concatenate horizontally
    #     imgs_comb = np.concatenate(
    #         [np.array(img.resize(min_shape)) for img in imgs], axis=1
    #     )
    #     imgs_comb = Image.fromarray(imgs_comb)

    #     if save:
    #         imgs_comb.save(img_path)
    #         return Path(img_path)
    #     else:
    #         imgs_comb.show()
    #         return imgs_comb

    def _render_rk_images(self, line: int, rk_size: int = 10,
                        images_shape: tuple[int, int] = (0, 0),
                        save: bool = False, img_path: str = "",
                        start_element: int = 0):
        """
        Internal method to render ranked list images.

        Adds blue border to query, green to correct matches,
        and red to incorrect ones.

        Returns:
            PIL.Image.Image or Path: combined image, or saved path.

        Raises:
            ValueError: if indices are invalid or ranked list is too short.
            RuntimeError: if required paths are missing.
        """
        # --- Sanity check for paths ---
        if not all((self.list_path, self.classes_path, self.images_path, self.rk_path)):
            raise RuntimeError("Missing required paths. Cannot render ranked list.")

        # --- Load classes ---
        classes_list = readData.read_classes(self.list_path, self.classes_path)

        # --- Load ranked lists (strings) ---
        with open(self.rk_path, "r") as f:
            all_lines = f.readlines()

        if line >= len(all_lines):
            raise ValueError(f"line index {line} out of range (max {len(all_lines)-1})")

        only_one = all_lines[line].split()
        if not only_one:
            raise ValueError(f"Ranked list at line {line} is empty.")

        # --- Load file list (image names) ---
        with open(self.list_path, "r") as f:
            list_test = [x.strip() for x in f.readlines()]

        # --- Check rk_size validity ---
        if rk_size + start_element > len(only_one):
            raise ValueError(
                f"Requested rk_size={rk_size} with start_element={start_element}, "
                f"but only {len(only_one)} elements available in ranked list."
            )

        # --- Build image paths and corresponding classes ---
        images_class_list = []
        images_show_list = []

        for i in range(rk_size):
            idx = int(only_one[i + start_element])

            if not (0 <= idx < len(classes_list)):
                raise ValueError(f"Index {idx} out of range for classes_list (len={len(classes_list)}).")
            if not (0 <= idx < len(list_test)):
                raise ValueError(f"Index {idx} out of range for list_test (len={len(list_test)}).")

            images_class_list.append(classes_list[idx])
            images_show_list.append(str(Path(self.images_path) / list_test[idx]))

        # --- Verify files exist ---
        for p in images_show_list:
            if not Path(p).is_file():
                raise FileNotFoundError(f"No such file: {p}")

        # --- Open all images ---
        imgs = [Image.open(p).convert("RGB") for p in images_show_list]

        # --- Draw borders ---
        ImageDraw.Draw(imgs[0]).rectangle(
            [(0, 0), (imgs[0].width, imgs[0].height)], outline="blue", width=10
        )
        for i in range(1, len(imgs)):
            color = "green" if images_class_list[0] == images_class_list[i] else "red"
            ImageDraw.Draw(imgs[i]).rectangle(
                [(0, 0), (imgs[i].width, imgs[i].height)], outline=color, width=10
            )

        # --- Decide resize shape ---
        if (
            isinstance(images_shape, tuple)
            and len(images_shape) == 2
            and all(isinstance(x, int) for x in images_shape)
        ):
            if images_shape == (0, 0):
                # safer resize: use min width and min height
                min_w = min(img.width for img in imgs)
                min_h = min(img.height for img in imgs)
                min_shape = (min_w, min_h)
            else:
                min_shape = images_shape
        else:
            raise ValueError("images_shape must be (int, int), e.g., (128, 128).")

        # --- Concatenate horizontally ---
        imgs_comb = np.concatenate(
            [np.array(img.resize(min_shape)) for img in imgs], axis=1
        )
        imgs_comb = Image.fromarray(imgs_comb)

        # --- Return/save result ---
        if save:
            imgs_comb.save(img_path)
            return Path(img_path)
        else:
            imgs_comb.show()
            return imgs_comb
