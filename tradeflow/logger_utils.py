import logging

from tradeflow.constants import Logger

logging.basicConfig(format=Logger.FORMAT, level=Logger.LEVEL)


def get_logger(name: str) -> logging.Logger:
    logger = logging.getLogger(name)
    return logger
