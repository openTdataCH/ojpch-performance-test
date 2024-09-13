"""Utility functions for file handling.

"""

import os

import configuration as config


def save_file(dir, file_name, text: str):
    joinnees = (config.FOLDERS["output"], dir, file_name) if dir else (config.FOLDERS["output"], file_name)
    file_path = os.path.join(*joinnees)
    with open(file=file_path, mode="w", encoding='utf-8') as file:
        file.write(str(text))

