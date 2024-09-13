"""Module for loading and handling test parameters of a given test run (series of API calls).

The module looks for configuration files in the folder "test_parameters" in the project.
- If there is a (first) command-line argument, this is understood as the parameter file-name.
- If not, it defaults to 'parameters.txt'
"""

import configuration as config
import sys
import os
from utilities import logging_wrapper as logging


par_dict = {}


def param(key: str, of_type: type = str) -> str or int or float:
    """Retrieve a value from the parameter file of type int, float or other (str).
    Fail fast (raise exception) if not available."""
    value = par_dict[key]
    return int(value) if of_type == int else (float(value) if of_type == float else str(value))


def param_true(key: str):
    """Same as parameter(), for a string meaning a boolean, 'true' or 'false', case-insensitive."""
    return param(key).lower() == 'true'


def set_param(key: str, value):
    """Set a parameter with a given key and value (object)."""
    par_dict[key] = value


def _load_parameters():
    # if there is a command-line argument, it is used as parameters file name, else, use default name:
    file_name = 'parameters.txt' if len(sys.argv) < 2 else sys.argv[1]
    file_path = os.path.join(config.FOLDERS["test_parameters"], file_name)
    with open(file=file_path, encoding='utf-8', mode='r') as parameters_file:
        lines = [l.strip() for l in parameters_file.readlines() if not l.strip().startswith('#') and '=' in l]
        for line in lines:
            key, value = line.split('=')[0].strip(), line.split('=')[1].strip()
            if key != '' and value != '':
                par_dict[key] = value
    logging.info(f"Loaded parameters from {file_path} file.")
    par_dict["parameters_file_name"] = file_name
    par_dict["parameters_file_path"] = file_path
    return file_name


# upon module load, perform:
_load_parameters()