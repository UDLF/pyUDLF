
def write_data(mtx, path):
    """Write a matrix (list of rows or 2D numpy array) as space separated text."""
    with open(path, "w") as f:
        for row in mtx:
            f.write(" ".join(str(x) for x in row))
            f.write("\n")
