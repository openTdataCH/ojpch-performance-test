"""A module with various functions to initialize a test run.

"""

import csv
import os
import random
import shutil
from datetime import datetime

import configuration as config
from utilities import logging_wrapper as logging
from utilities import object_store as store
from utilities import stop_points
from utilities.parameters import param, param_true


def set_random_seed():
    if param_true('use_random_seed'):
        seed = param('random_seed', int)
        logging.info(f"Using fixed random_seed {seed} (to get same random data in next run).")
        random.seed(seed)


def prepare_directories():
    for dir in (config.FOLDERS["output"], ):
        if not os.path.exists(dir):
            os.mkdir(dir)


def remove_old_test_directories():
    if param_true('remove_old_test_directories'):
        test_dirs = [d for d in os.listdir(config.FOLDERS["output"]) if d.startswith('test') and
                     os.path.isdir(os.path.join(config.FOLDERS["output"], d))]
        for test_dir in test_dirs:
            shutil.rmtree(os.path.join(config.FOLDERS["output"], test_dir))
        logging.info(f"Removed old test directories {test_dirs}.")


def create_test_directory():
    parameters_file = param("parameters_file_name")
    t_dir = 'test_' + parameters_file.replace('.txt', '_') + datetime.now().strftime("%Y-%m-%d_%H.%M.%S")
    store.put("test_directory", t_dir)
    os.mkdir(os.path.join(config.FOLDERS["output"], t_dir))
    if param_true('save_details'):
        shutil.copy2(os.path.join(config.FOLDERS["test_parameters"], parameters_file),
                     os.path.join(config.FOLDERS["output"], t_dir, '_' + parameters_file))
    logging.info(f"Created test directory {t_dir}.")


def load_connections_file():
    if param_true('use_connections_file'):
        conn_file_path = os.path.join(config.FOLDERS["test_parameters"], param('connections_file'))
        with open(file=conn_file_path, newline='', encoding='utf-8') as file:
            csvreader = csv.reader(file, delimiter=param('connections_delimiter'))
            connections = [[p.strip() for p in r[1:] if p.strip()] for r in csvreader][1:]
            store.put("connections", connections)
            logging.info(f"Loaded connections file {conn_file_path} with {len(connections)} connections.")

        for row in connections:
            for place in row:
                if not stop_points.get_by_name(place):
                    raise ValueError(f"ERROR: no service point known for name '{place}'. ABORT")
        logging.info(f"Connections from connections file are ready and valid.")

