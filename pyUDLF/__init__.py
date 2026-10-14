"""
pyUDLF: Python wrapper for UDLF, the Unsupervised Distance Learning Framework.

    from pyUDLF import UDLF

    udlf = UDLF()
    res = udlf.run("CPRR", ranked_lists=rks, params={"k": 20}, classes=labels)
    res.ranked_lists, res.map_before, res.map_after

The legacy API (pyUDLF.run_calls, pyUDLF.utils.inputType) is still available.
Warnings and errors are logged with the standard logging module; call
pyUDLF.enable_logging("INFO") to also see informative messages.
"""

__version__ = "0.9.0.dev0"

from pyUDLF.api import UDLF, Result
from pyUDLF.errors import UDLFError, UDLFNotFoundError, UDLFParamError, UDLFRunError
from pyUDLF.utils.logger import enable_logging

__all__ = ["UDLF", "Result", "UDLFError", "UDLFNotFoundError", "UDLFParamError",
           "UDLFRunError", "enable_logging", "__version__"]
