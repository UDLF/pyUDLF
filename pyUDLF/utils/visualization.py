from pathlib import Path
import numpy as np
from PIL import Image, ImageDraw
from pyUDLF.utils import readData
from pyUDLF.utils.logger import get_logger

logger = get_logger(__name__)

def render_ranked_list(
    rk_path: str,
    list_path: str,
    classes_path: str,
    images_path: str,
    line: int,
    rk_size: int = 10,
    images_shape: tuple[int, int] = (0, 0),
    save: bool = False,
    img_path: str = "",
    start_element: int = 0,
):
    """
    Render a ranked list (input or output) as concatenated images.

    Args:
        rk_path (str): path to the ranked list file.
        list_path (str): path to the list file.
        classes_path (str): path to the classes file.
        images_path (str): directory containing dataset images.
        line (int): line index in the ranked list file (query index).
        rk_size (int): number of retrieved elements to show.
        images_shape (tuple[int, int]): resize shape (w,h). If (0,0), use min size.
        save (bool): if True, save to disk instead of showing.
        img_path (str): path to save the image if save=True.
        start_element (int): offset in ranked list.

    Returns:
        PIL.Image.Image or Path: combined image, or saved path.
    """
    # --- Sanity checks ---
    if type(line) is not int or line < 0:
        raise ValueError(f"line must be a non-negative integer, got {line!r}")

    for p in [rk_path, list_path, classes_path]:
        if not Path(p).is_file():
            raise FileNotFoundError(f"Required file not found: {p}")
    if not Path(images_path).is_dir():
        raise FileNotFoundError(f"Images directory not found: {images_path}")

    # --- Load classes ---
    classes_list = readData.read_classes(list_path, classes_path)

    # --- Load ranked lists ---
    with open(rk_path, "r") as f:
        all_lines = f.readlines()

    if line >= len(all_lines):
        raise ValueError(f"line index {line} out of range (max {len(all_lines)-1})")

    only_one = all_lines[line].split()
    if not only_one:
        raise ValueError(f"Ranked list at line {line} is empty.")

    # --- Load file list (image names) ---
    with open(list_path, "r") as f:
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
        images_show_list.append(str(Path(images_path) / list_test[idx]))

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
        and all(type(x) is int for x in images_shape)
    ):
        if images_shape == (0, 0):
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
        logger.info("Saved ranked list visualization at %s", img_path)
        return Path(img_path)
    else:
        imgs_comb.show()
        return imgs_comb
