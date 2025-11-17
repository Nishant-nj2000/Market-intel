import logging
import sys
from pathlib import Path

def setup_logger(name="marketintel", level=logging.INFO, logfile: str = "marketintel.log"):
    logger = logging.getLogger(name)
    if logger.handlers:
        return logger
    logger.setLevel(level)
    fmt = logging.Formatter("%(asctime)s — %(levelname)s — %(name)s — %(message)s")
    sh = logging.StreamHandler(sys.stdout)
    sh.setFormatter(fmt)
    logger.addHandler(sh)
    fh = logging.FileHandler(logfile)
    fh.setFormatter(fmt)
    logger.addHandler(fh)
    return logger

logger = setup_logger()