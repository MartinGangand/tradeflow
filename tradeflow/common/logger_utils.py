import logging

FORMAT = "%(asctime)s [%(filename)s] [%(levelname)s] - %(message)s"
LEVEL = logging.INFO

logging.basicConfig(format=FORMAT, level=LEVEL)


def get_logger(name: str) -> logging.Logger:
    logger = logging.getLogger(name)
    return logger
