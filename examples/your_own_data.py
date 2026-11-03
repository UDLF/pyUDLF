"""
Run a method on your own data, from the command line.

    python examples/your_own_data.py \
        --ranked-lists my_ranked_lists.txt --lists my_lists.txt --classes my_classes.txt \
        --method CPRR --param l=400 --param k=20 --output reranked.txt

    python examples/your_own_data.py --matrix my_distances.txt --matrix-type dist ...
    python examples/your_own_data.py --features my_features.npy --classes-list labels.txt ...

Inputs (UDLF formats, see the README):
  --ranked-lists  one line per query with element indices (or names, with --lists)
  --matrix        N lines with N distances or similarities
  --features      .npy array (N x D): ranked lists by Euclidean distance are built
  --lists         one element name per line, in dataset order
  --classes       one "name:class" per line (needs --lists)
  --classes-list  one class label per line, in dataset order

Without arguments it runs on the synthetic dataset of the repository.
"""

import argparse
from pathlib import Path

import numpy as np

from pyUDLF import UDLF

DATA = Path(__file__).resolve().parent.parent / "tests" / "data" / "synthetic"


def parse_value(text):
    for convert in (int, float):
        try:
            return convert(text)
        except ValueError:
            pass
    return {"true": True, "false": False}.get(text.lower(), text)


def ranked_lists_from_features(path):
    features = np.load(path).astype(np.float64)
    squares = (features ** 2).sum(axis=1)
    # Euclidean distances without an N x N x D intermediate array
    distances = np.sqrt(np.maximum(squares[:, None] + squares[None, :]
                                   - 2 * features @ features.T, 0))
    return np.argsort(distances, axis=1, kind="stable")


def main():
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    source = parser.add_mutually_exclusive_group()
    source.add_argument("--ranked-lists")
    source.add_argument("--matrix")
    source.add_argument("--features")
    parser.add_argument("--matrix-type", default="dist", choices=["dist", "sim"])
    parser.add_argument("--lists")
    labels = parser.add_mutually_exclusive_group()
    labels.add_argument("--classes")
    labels.add_argument("--classes-list")
    parser.add_argument("--method", default="CPRR")
    parser.add_argument("--param", action="append", default=[], metavar="NAME=VALUE",
                        help="method parameter, e.g. --param k=20 (see `pyudlf describe CPRR`)")
    parser.add_argument("--output", help="file for the re-ranked lists")
    args = parser.parse_args()

    if not (args.ranked_lists or args.matrix or args.features):
        print("No input given: using the synthetic dataset of the repository.\n")
        args.ranked_lists = str(DATA / "rk_num.txt")
        args.lists, args.classes = str(DATA / "lists.txt"), str(DATA / "classes.txt")
        args.param = args.param or ["l=100", "k=10"]

    params = dict(item.split("=", 1) for item in args.param)
    params = {name: parse_value(value) for name, value in params.items()}
    classes = args.classes
    if args.classes_list:
        classes = Path(args.classes_list).read_text().split()

    inputs = {}
    if args.matrix:
        inputs = {"matrix": args.matrix, "matrix_type": args.matrix_type}
    elif args.features:
        inputs = {"ranked_lists": ranked_lists_from_features(args.features)}
    else:
        inputs = {"ranked_lists": args.ranked_lists}

    res = UDLF().run(args.method, params=params, classes=classes, names=args.lists, **inputs)

    print(res)
    if res.metrics:
        print(f"{'':10s} {'before':>8s} {'after':>8s}")
        for name in res.metrics["after"]:
            print(f"{name:10s} {res.metrics['before'][name]:8.4f} {res.metrics['after'][name]:8.4f}")
    print(f"Time: {res.time:.3f} s")
    if args.output:
        np.savetxt(args.output, res.ranked_lists, fmt="%d")
        print(f"Re-ranked lists saved to {args.output}")


if __name__ == "__main__":
    main()
