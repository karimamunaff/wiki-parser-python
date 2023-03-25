import logging
from pathlib import Path
import sys

LOGGING_DIRECTORY = Path(__file__).resolve().parents[1] / "logs"
LOGGING_DIRECTORY.mkdir(parents=True, exist_ok=True)


def get_logger(filename: str):
    filename = Path(filename).stem
    log_filepath = LOGGING_DIRECTORY / f"{filename}.log"
    file_handler = logging.FileHandler(filename=log_filepath)
    stdout_handler = logging.StreamHandler(stream=sys.stdout)
    handlers = [file_handler, stdout_handler]

    logging.basicConfig(
        level=logging.DEBUG,
        format="[%(asctime)s] {%(filename)s:%(lineno)d} %(levelname)s - %(message)s",
        handlers=handlers,
    )

    logger = logging.getLogger(filename)
    return logger
