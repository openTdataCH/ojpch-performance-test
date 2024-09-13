
import csv
import math
import os
import statistics

import configuration as config
from utilities import logging_wrapper as logging
from utilities import object_store as store
from utilities.datetime_utils import utc_now_iso
from utilities.file_utils import save_file

NA = 'n/a'
RESULTS_TABLE_HEADERS = ["nr", "environment", "request_type", "origin_name", "origin_didok", "origin_lon",
                         "origin_lat", "dest_name", "dest_didok", "dest_lon", "dest_lat", "via_name", "via_didok",
                         "via_lon", "via_lat", "arrdeptime", "calc_time", "response_size", "return_code"]


def _calc_percentile(array, percentile):
    # credits: https://www.delftstack.com/howto/python/python-percentile/
    return sorted(array)[int(math.ceil((len(array) * percentile) / 100)) - 1]


def new_results_table():
    return [RESULTS_TABLE_HEADERS]


def compute_statistics():
    n = len(store.fetch("results_table")) - 1
    ct200 = [row[16] for row in store.fetch("results_table") if row[18].startswith('200')]
    n200 = len(ct200)
    ctmin, ctmax, ctavg, ctp50, ctp90, ctp95 = NA, NA, NA, NA, NA, NA
    if n200 > 0:
        ctavg = round(1000 * statistics.mean(ct200))
        ctmin = round(1000 * min(ct200))
        ctmax = round(1000 * max(ct200))
        ctp50 = round(1000 * _calc_percentile(ct200, 50.0))
        ctp90 = round(1000 * _calc_percentile(ct200, 90.0))
        ctp95 = round(1000 * _calc_percentile(ct200, 95.0))

    stat = {'timestamp': utc_now_iso(),
            'use_parameters': store.fetch("use_pars"),
            'environment': store.fetch("environment"), 'request': store.fetch("request_type"),
            'n200': n200, 'n': n, 'ctavg': ctavg, 'ctmin': ctmin, 'ctmax': ctmax,
            'ctp50': ctp50, 'ctp90': ctp90, 'ctp95': ctp95}

    store.fetch("stats").append(stat)


def save_statistics():
    stat = 'Test Statistics'
    stat += '\nService                                      number of tests                                                   calc. time [ms]'
    stat += '\nenvironment  request type        total         ok     not_ok        min    average        p50        p90        p95        max'
    for e in store.fetch("stats"):
        rt_plus = e['request'] + ("+" if e['use_parameters'] else "")
        stat += f"\n{e['environment']:12s} {rt_plus:14s} {e['n']:10d} {e['n200']:10d} {e['n'] - e['n200']:10d}"
        stat += f" {e['ctmin']:10d} {e['ctavg']:10d} {e['ctp50']:10d} {e['ctp90']:10d} {e['ctp95']:10d} {e['ctmax']:10d}" if \
            e['n200'] > 0 else '        n/a        n/a        n/a        n/a        n/a        n/a'

    logging.info('STATISTICS:\n' + stat)
    save_file(store.fetch("test_directory"), '_statistics.txt', stat)
    save_file(None, 'latest_statistics.txt', stat)


def save_results_table_csv_file():
    env, rt = store.fetch("environment"), store.fetch("request_type")
    path = os.path.join(config.FOLDERS["output"], store.fetch("test_directory"), env + "_" + rt + "_results_table.csv")
    with open(file=path, mode="w", newline="", encoding='utf-8') as file:
        writer = csv.writer(file, delimiter=";")
        for row in store.fetch("results_table"):
            writer.writerow(row)
