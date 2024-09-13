"""A wrapper for logging, based on the builtin logging library.

"""

import logging
import os
import shutil
import sys

import configuration as config
from utilities import object_store as store


# logging to console and/or to file: - comment-out the lines that are not needed:
if not os.path.exists(config.FOLDERS["output"]):
    os.mkdir(config.FOLDERS["output"])


LOG_FILE = os.path.join(config.FOLDERS["output"], 'latest_log.txt')
if not os.path.exists(LOG_FILE):
    with open(file=LOG_FILE, mode="w") as f:
        f.write("")

LOG_HANDLERS = [
    logging.StreamHandler(sys.stdout),
    logging.FileHandler(LOG_FILE, 'w', 'utf-8'),
]
logging.basicConfig(handlers=LOG_HANDLERS, level=logging.INFO, format='%(asctime)s: %(levelname)s: %(message)s')


def warning(*args):
    logging.warning(*args)


def info(*args):
    logging.info(*args)


def log1connection(nr: int, env: str, req: str, a: str, b: str, via: str, ms: int, bytes: int, code_n_reason: str,
                   message=""):
    message_text = "/" + message if message else ""
    to_text = " to " + b if b and b != "n/a" else ""
    via_text = " via " + via if via and via != "n/a" else ""
    logging.info(f"{nr:02d} {env:9s} {req:11s}:{ms:>5d} ms,{bytes:>8d} B., {code_n_reason}{message_text} "
                 f"({a}{to_text}{via_text}).")


def copy_log_file_to_test_directory():
    if os.path.exists(LOG_FILE):
        shutil.copy2(LOG_FILE, os.path.join(config.FOLDERS["output"], store.fetch("test_directory"), '_log.txt'))

