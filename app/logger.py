import logging

def get_logger():
    logger = logging.getLogger("ScannerLogger")
    logger.setLevel(logging.DEBUG)

    fh = logging.FileHandler("logs/scanner.log")
    ch = logging.StreamHandler()

    formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
    fh.setFormatter(formatter)
    ch.setFormatter(formatter)

    logger.addHandler(fh)
    logger.addHandler(ch)

    return logger
