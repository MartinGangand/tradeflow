import logging
import sys

from tradeflow.constants import Logger

logging.basicConfig(format=Logger.FORMAT, level=Logger.LEVEL)


def get_logger(name: str, print_to_stdout=True) -> logging.Logger:
    logger = logging.getLogger(name)
    if print_to_stdout:
        handler = create_stdout_handler()
        logger.addHandler(handler)
    return logger


def create_stdout_handler() -> logging.StreamHandler:
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(logging.Formatter(fmt=Logger.FORMAT))
    handler.setLevel(level=Logger.LEVEL)
    return handler
