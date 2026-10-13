"""
Exceptions raised by the pyUDLF API (pyUDLF.UDLF).

All of them derive from UDLFError, and also from the matching built-in
exception, so ``except ValueError`` / ``except FileNotFoundError`` work too.
"""


class UDLFError(Exception):
    """Base class of every pyUDLF error."""


class UDLFParamError(UDLFError, ValueError):
    """Invalid method, parameter or input, detected before running UDLF."""


class UDLFNotFoundError(UDLFError, FileNotFoundError):
    """The UDLF binary was not found."""


class UDLFRunError(UDLFError, RuntimeError):
    """UDLF failed, or replaced a value given by the user with its default.

    Attributes:
        problems (list[str]): what went wrong.
        output (str): everything UDLF printed.
        config (str): text of the config file used in the run.
    """

    def __init__(self, problems, output="", config=""):
        self.problems = list(problems)
        self.output = output
        self.config = config
        tail = "\n".join(output.rstrip().splitlines()[-15:])
        message = "; ".join(self.problems)
        if tail:
            message += f"\nLast lines printed by UDLF:\n{tail}"
        super().__init__(message)
