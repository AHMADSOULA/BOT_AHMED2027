import logging
import os
import colorlog
from config import config

os.makedirs(config.LOG_DIR, exist_ok=True)

def get_logger(name):
    logger = logging.getLogger(name)
    if logger.handlers: return logger
    logger.setLevel(logging.INFO)
    ch = logging.StreamHandler()
    ch.setFormatter(colorlog.ColoredFormatter(
        "%(log_color)s[%(asctime)s] [%(levelname)s] [%(name)s] %(message)s",
        datefmt="%H:%M:%S",
        log_colors={'DEBUG': 'cyan', 'INFO': 'green', 'WARNING': 'yellow', 'ERROR': 'red', 'CRITICAL': 'bold_red'}
    ))
    logger.addHandler(ch)
    return logger
