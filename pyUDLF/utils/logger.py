"""
Logging of pyUDLF.

pyUDLF uses the standard logging module, under the "pyUDLF" logger, and does
not install handlers itself. By default Python shows warnings and errors on
stderr and hides informative messages. To see them (as in older versions):

    import pyUDLF
    pyUDLF.enable_logging("INFO")          # or "DEBUG"

or configure logging as usual in your application, e.g.
logging.basicConfig(level=logging.INFO).
"""

import logging

LOGGER_NAME = "pyUDLF"


def get_logger(name: str) -> logging.Logger:
    """Return the logger of a pyUDLF module (no handler is installed)."""
    return logging.getLogger(name)


def enable_logging(level="INFO") -> logging.Logger:
    """
    Show pyUDLF messages from `level` on (e.g. "INFO", "DEBUG", "WARNING")
    on stderr, formatted as "[LEVEL] message". Calling it again only changes
    the level.

    Returns:
        logging.Logger: the "pyUDLF" logger.
    """
    logger = logging.getLogger(LOGGER_NAME)
    for handler in list(logger.handlers):
        if getattr(handler, "_pyudlf", False):
            logger.removeHandler(handler)
    handler = logging.StreamHandler()
    handler.setFormatter(logging.Formatter("[%(levelname)s] %(message)s"))
    handler._pyudlf = True
    logger.addHandler(handler)
    logger.setLevel(level)
    logger.propagate = False  # avoid duplicates when the root logger has handlers
    return logger
