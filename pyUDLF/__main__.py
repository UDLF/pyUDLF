"""
Command line of pyUDLF:

    pyudlf download [--version 1.70] [--dest DIR] [--force]
    pyudlf where
    pyudlf methods
    pyudlf describe METHOD

(also available as `python -m pyUDLF ...`)
"""

import argparse
import sys

from pyUDLF import __version__, install
from pyUDLF.api import UDLF
from pyUDLF.errors import UDLFError


def main(argv=None):
    parser = argparse.ArgumentParser(
        prog="pyudlf", description="pyUDLF: Python wrapper for UDLF.")
    parser.add_argument("--version", action="version", version=f"pyUDLF {__version__}")
    commands = parser.add_subparsers(dest="command", required=True)

    download = commands.add_parser(
        "download", help="download and install the official UDLF binary")
    download.add_argument("--version", dest="udlf_version", default=None,
                          choices=sorted(install.RELEASES),
                          help=f"UDLF version (default: {install.DEFAULT_VERSION})")
    download.add_argument("--dest", default=None,
                          help=f"installation directory (default: {install.pyudlf_home()})")
    download.add_argument("--force", action="store_true",
                          help="download again even if UDLF is already installed")

    commands.add_parser("where", help="show the UDLF binary that pyUDLF uses")
    commands.add_parser("methods", help="list the UDLF methods")
    describe = commands.add_parser("describe", help="show the parameters of a method")
    describe.add_argument("method")

    args = parser.parse_args(argv)
    try:
        if args.command == "download":
            path = install.download_udlf(args.udlf_version, args.dest, args.force)
            print(f"UDLF installed at {path}")
        elif args.command == "where":
            print(UDLF().bin_path)
        elif args.command == "methods":
            print("\n".join(UDLF.methods()))
        elif args.command == "describe":
            print(UDLF.describe(args.method))
    except UDLFError as e:
        print(f"error: {e}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
