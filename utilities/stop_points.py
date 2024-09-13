"""A module for loading and handling the stop points data (stations and bus stops in Switzerland).
Loads the data to folder "stop_points".

This is a replacement for the old, decommissioned DIDOK data.
"""
import os
import requests
import shutil
import csv
import configuration as config
from utilities import logging_wrapper as logging


sp_dict = {}
sp_columns = None
keys = None


def keys():
    return keys


def get_by_name(name: str):
    return sp_dict.get(name)


def _load_sp():
    global sp_dict, sp_columns, keys

    sp_dir = config.FOLDERS["stop_points"]
    if not os.path.exists(sp_dir):
        os.mkdir(sp_dir)

    if len([f for f in os.listdir(sp_dir) if f.endswith(".csv")]) < 1:
        sp_data = requests.get(config.SP_PERMALINK)
        sp_zip_file = os.path.join(sp_dir, 'sp_temp.zip')
        with open(sp_zip_file, mode='wb') as file:
            file.write(sp_data.content)
        logging.info(
            f"Loaded service points zip file from {config.SP_PERMALINK}, {len(sp_data.content)} bytes.")
        shutil.unpack_archive(sp_zip_file, sp_dir)
        os.remove(sp_zip_file)
        logging.info(f"Unzipped it to folder {sp_dir}.")

    sp_file = os.listdir(sp_dir)[0]
    sp_path = os.path.join(sp_dir, sp_file)
    if not os.path.exists(sp_path) or sp_file[-4:] != ".csv":
        raise f"ERROR: load_sp() failed, has no valid CSV service points file at {sp_path}"

    with open(file=sp_path, newline='', encoding='utf-8-sig') as csv_file:
        csv_reader = csv.reader(csv_file, delimiter=';')
        for row in csv_reader:
            if sp_columns == None:
                sp_columns = list(row)
            if 'ch:1:sloid' in _sp_value(row, "sloid") and _sp_value(row, "uicCountryCode") == '85':  # Swiss SP only
                if _sp_value(row, "stopPoint") == 'true':
                    try:
                        lon, lat = _sp_value(row, "wgs84East"), _sp_value(row, "wgs84North")
                        if lon and lat:
                            name = _sp_value(row, "designationOfficial")
                            sp_dict[name] = StopPoint(_sp_value(row, "sloid"), int(_sp_value(row, "number")),
                                                   name, float(lon), float(lat))
                    except:
                        logging.warning(f"WARN: ignore {row}")
    keys = list(sp_dict.keys())
    count = len(keys)
    logging.info(f"Loaded stop_points module with {count} Swiss stop points from file {sp_path}.")


def _sp_value(row: list, column: str):
    for i, x in enumerate(sp_columns):
        if column == x:
            return row[i]
    return None


class StopPoint:
    def __init__(self, sloid: str, number: int, name: str, lon: float, lat: float):
        self.number = number
        self.sloid = sloid
        self.name = name
        self.lon = lon
        self.lat = lat

# call when the module is loaded:
_load_sp()