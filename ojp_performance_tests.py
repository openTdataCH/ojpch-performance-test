"""
A python script to run performance tests of an OJP (Open API for distributed journey planning) API service.

See: https://github.com/openTdataCH/ojpch-performance-test

2023-11-08 - Matthias Günter, Diogo Ferreiro, Markus Meier
"""

import csv
import json
import logging
import math
import os.path
import random
import shutil
import statistics
import sys
import time
import xml.dom.minidom
from datetime import datetime, timedelta, date
from utilities.template_util import Template

import requests

import configuration as config

# global variables:
didoklist = []
csvheaders = ["nr", "environment", "request_type",
              "origin_name", "origin_didok", "origin_lon", "origin_lat",
              "dest_name", "dest_didok", "dest_lon", "dest_lat",
              "via_name", "via_didok", "via_lon", "via_lat",
              "arrdeptime", "calc_time", "response_size", "return_code"]
par_dict = {}
connections = None
didok_for_places = None

# logging to console and/or to file: - comment-out those lines not needed:
LOG_FILE = './output/latest_log.log'
LOG_HANDLERS = [
    logging.StreamHandler(sys.stdout),
    # logging.FileHandler(LOG_FILE, 'w', 'utf-8'),
]
logging.basicConfig(handlers=LOG_HANDLERS, level=logging.INFO, format='%(asctime)s: %(levelname)s: %(message)s')

NA = 'n/a'


def load_parameters():
    # if there is a command-line argument, it is used as parameters file name, else, use default name:
    file_name = config.INPUT_PARAMETERS_DEFAULT if len(sys.argv) < 2 else sys.argv[1]
    file_path = os.path.join(config.INPUT, file_name)
    with open(file=file_path, encoding='utf-8', mode='r') as parameters_file:
        lines = [l.strip() for l in parameters_file.readlines() if not l.strip().startswith('#') and '=' in l]
        for line in lines:
            key, value = line.split('=')[0].strip(), line.split('=')[1].strip()
            if key != '' and value != '':
                par_dict[key] = value
    logging.info(f"Loaded parameters from {file_path} file.")
    return file_name


def parameter(key: str, of_type: type = str) -> str or int or float:
    """Retrieve a value from the parameter file of type int, float or other (str).
    Fail fast (raise exception) if not available."""
    value = par_dict[key]
    return int(value) if of_type == int else (float(value) if of_type == float else str(value))


def parameter_true(key: str):
    """Same as parameter(), for a string meaning a boolean, 'true' or 'false', case-insensitive."""
    return parameter(key).lower() == 'true'


def set_random_seed():
    if parameter_true('use_random_seed'):
        seed = parameter('random_seed', int)
        logging.info(f"Using fixed random_seed {seed} (to get same random data in next run).")
        random.seed(seed)


def load_didok():
    didok_file = os.path.join(config.DATA, config.DIDOK_FILE)
    if parameter_true('download_didok_data') or not os.path.exists(didok_file):
        didok_data = requests.get(config.DIDOK_PERMALINK)
        with open(config.DATA + '/' + config.DIDOK_FILE, mode='wb') as file:
            file.write(didok_data.content)
        logging.info(
            f"Loaded DIDOK file {config.DIDOK_FILE} from {config.DIDOK_PERMALINK}, {len(didok_data.content)} bytes.")

    with open(file=os.path.join(config.DATA, config.DIDOK_FILE), newline='', encoding='utf-8') as file:
        csv_reader = csv.reader(file, delimiter=';')
        for row in csv_reader:
            if 'ch:1:sloid' in row[0]:
                didoklist.append(row)
    logging.info(f"Loaded {len(didoklist)} stations/stops from DIDOK file {config.DIDOK_FILE}.")


def prepare_directories():
    for dir in (config.OUTPUT, config.DATA):
        if not os.path.exists(dir):
            os.mkdir(dir)


def remove_old_test_directories():
    if parameter_true('remove_old_test_directories'):
        test_dirs = [d for d in os.listdir(config.OUTPUT) if d.startswith('test') and
                     os.path.isdir(os.path.join(config.OUTPUT, d))]
        for test_dir in test_dirs:
            shutil.rmtree(os.path.join(config.OUTPUT, test_dir))
        logging.info(f"Removed old test directories {test_dirs}.")


def create_test_directory(parameter_file):
    test_directory = 'test_' + parameter_file.replace('.txt', '_') + datetime.now().strftime("%Y_%m_%d_%H_%M_%S")
    os.mkdir(os.path.join(config.OUTPUT, test_directory))
    if parameter_true('save_details'):
        shutil.copy2(os.path.join(config.INPUT, parameter_file),
                     os.path.join(config.OUTPUT, test_directory, '_' + parameter_file))
    logging.info(f"Created test directory {test_directory}.")
    return test_directory


def lir_for_stop(session, stop_name: str) -> str:
    lir_simple = Template('LIR_simple')
    lir_simple.replace('timestamp', datetime.utcnow().isoformat() + 'Z')
    lir_simple.replace('location_name', stop_name)
    response, ct = http_post(session, list(config.ENVIRONMENTS.keys())[0], str(lir_simple))
    resp_text = response.content.decode('utf-8')
    stop_place_ref = find_xml_element(resp_text, '<ojp:StopPlaceRef>')
    location_name = find_xml_element(resp_text, '<ojp:Text xml:lang="de">')
    lon = rnd(float(find_xml_element(resp_text, '<siri:Longitude>')))
    lat = rnd(float(find_xml_element(resp_text, '<siri:Latitude>')))
    logging.info(f"LIR for stop {stop_name} found {stop_place_ref} / {location_name}.")
    return stop_place_ref, location_name, (lon, lat)


def load_connections_file():
    global connections, didok_for_places

    if parameter_true('use_connections_file'):
        didok_for_places_path = os.path.join(config.DATA, config.DIDOK_FOR_PLACES)
        didok_for_places = {}
        if os.path.exists(didok_for_places_path):
            with open(file=didok_for_places_path, encoding='utf-8', mode='r') as file:
                didok_for_places = json.loads(file.read())
            logging.info(f"Loaded existing file {didok_for_places_path} with {len(didok_for_places.keys())} DIDOK codes.")

        count = 0
        conn_file_path = os.path.join(config.INPUT, parameter('connections_file'))
        with open(file=conn_file_path, newline='', encoding='utf-8') as file:
            csvreader = csv.reader(file, delimiter=parameter('connections_delimiter'))
            connections = [[p.strip() for p in r[1:] if p.strip()] for r in csvreader][1:]
            logging.info(f"Loaded connections file {conn_file_path} with {len(connections)} connections.")

        session = requests.Session()
        for row in connections:
            for place in row:
                if didok_for_places.get(place) is None:
                    stop_place_ref, location_name, coords = lir_for_stop(session, place)
                    didok_for_places[place] = (stop_place_ref, location_name, coords)
                    count += 1
        with open(file=didok_for_places_path, encoding='utf-8', mode='w') as file:
            file.write(json.dumps(didok_for_places, indent=2, ensure_ascii=False, sort_keys=True))
        logging.info(f"Added {count} DIDOK codes and saved file {didok_for_places_path}.")


def add_random_offset_to_coord(coords_lon_lat: tuple, max_radius: float):
    """Randomly offset a point at a given coordinate by max_radius. Using uniform random distribution.
    Using an approximative formula which is ~ 1 % precise for Switzerland."""
    p = (1.0, 1.0)
    while math.sqrt(p[0] * p[0] + p[1] * p[1]) >= 1.0:  # find a random point within a circle of radius 1.0:
        p = (2.0 * random.random() - 1.0, 2.0 * random.random() - 1.0)
    return (coords_lon_lat[0] + max_radius * 0.01314 * p[0], coords_lon_lat[1] + max_radius * 0.00900 * p[1])


def select_didok_place(role: str, call_number: int) -> (str, int, tuple):
    """Select a stop (name, DIDOK code, coords) either randomly from the given didok table,
    or from a connections file."""
    if parameter_true('use_connections_file'):
        conn = connections[(call_number - 1) % len(connections)]  # if call_number exceeds # connections, cycle around
        conn = conn + [None, None]  # to avoid out-of-bounds errors

        assert conn[1]; "ERROR: connections file must always contain a 'from' and a 'to' value!"
        assert conn[0] != conn[1] and conn[0] != conn[2] and conn[1] != conn[2]; \
            f"ERROR: connections file from={conn[0]}, to={conn[1]} and via={conn[2]} must all be different!"

        place = conn[0] if role == 'origin' else conn[1] if role == 'destination' else conn[2]
        if place:
            didok_for_place = didok_for_places.get(place)
            if didok_for_place:
                return didok_for_place[1], didok_for_place[0], didok_for_place[2]
        return NA, NA, (0.0, 0.0)
    else:
        while True:
            p = didoklist[random.randrange(0, len(didoklist))]
            p_didok = p[22][0:7]  # remove check number
            p_name = p[25]
            try:
                p_coords = [float(p[19]), float(p[20])]
                if parameter_true('use_geopos'):
                    p_coords = add_random_offset_to_coord(p_coords, parameter('max_dist_from_stop', float))
                break
            except:
                logging.debug(f"-  ... {role} {p_name} / {p_didok} has no coordinates -> repeat.")
        return p_name, p_didok, p_coords


def select_date_time_at_random() -> str:
    """Select a random departure date/time, within the bounds given by the parameters."""
    days_ahead_min, days_ahead_max = parameter('days_ahead_min', int), parameter('days_ahead_max', int)
    hours_min, hours_max = parameter('hours_min', int), parameter('hours_max', int)
    minutes_min, minutes_max = parameter('minutes_min', int), parameter('minutes_max', int)

    days_ahead = random.randrange(days_ahead_min, days_ahead_max + 1)
    hours = random.randrange(hours_min, hours_max + 1)
    minutes = random.randrange(minutes_min, minutes_max + 1)

    date_ahead = date.today() + timedelta(days=days_ahead)
    return datetime(date_ahead.year, date_ahead.month, date_ahead.day, hours, minutes, 0).isoformat()


def rnd(f: float, decimal_digits=6):
    """Round float number to the given decimal_digits."""
    return float(('{:.' + str(decimal_digits) + 'f}').format(f))


def pretty_print_xml(ugly_xml: str) -> str:
    try:
        dom = xml.dom.minidom.parseString(ugly_xml)
        xml_str = dom.toprettyxml()
        return '\n'.join([line for line in xml_str.split('\n') if line.strip()])  # remove empty lines
    except Exception as e:
        return ugly_xml


def pretty_print_json(ugly_json: str) -> str:
    try:
        return json.dumps(json.loads(ugly_json), indent=2, ensure_ascii=False, sort_keys=False)
    except Exception as e:
        return ugly_json


def apply_params_and_restrictions(request: Template):
    # try to insert everything, regardless of the given request type - will be ignored if no placeholder in template:
    for par in ('tr_include_track_sections', 'tr_include_leg_projection', 'tr_include_turn_description',
                'tr_include_intermediate_stops', 'ser_operator_exclude', 'ser_operator_ref',
                'ser_include_previous_calls', 'ser_include_onward_calls', 'ser_include_realtime_data',
                'lir_include_pt_modes', 'tir_include_calls', 'tir_include_track_sections', 'tir_include_service',
                'trias2020tr_include_track_sections', 'trias2020tr_include_leg_projection',
                'trias2020tr_include_intermediate_stops'):
        # Parameter is set to 'true' if main switch use_params=True AND par_xy=True:
        value = str(parameter_true('use_params') and parameter_true(par)).lower()
        request.replace(par, value)

    # other, non-boolean OJP parameters:
    for par in ('ser_number_of_results', 'ser_stop_event_type_reference', 'ser_operator_exclude', 'ser_operator_ref',
                'lir_geo_restriction_type', 'lir_number_of_results', 'trias2020tr_number_of_results',
                'tr_number_of_results'):
        request.replace(par, parameter(par))


def find_xml_element(xml_str: str, element_name: str):
    i1 = xml_str.find(element_name)
    i2 = xml_str.find('<', i1 + len(element_name))
    return xml_str[i1 + len(element_name):i2] if i1 >= 0 and i2 >= 0 else None


def build_request(env: str, session: requests.Session, rt: str, test_directory: str, call_number: int) -> (list, str):
    """Build a request for the given type, with random parameters filled-in;
    if not successfull (in case of a TIR), return "None"."""
    d_name, d_didok, d_coords = NA, NA, (0.0, 0.0)
    v_name, v_didok, v_coords = NA, NA, (0.0, 0.0)

    arrdeptime = select_date_time_at_random() if rt in ('TR', 'SER', 'TIR', 'TRIAS2020TR', 'J-S-TRIPSOD') else NA

    # choose random origin (and destination for TR) from didok:
    o_name, o_didok, o_coords = select_didok_place('origin', call_number)
    if rt in ('TR', 'TIR', 'TRIAS2020TR', 'J-S-TRIPSOD'):
        while True:
            d_name, d_didok, d_coords = select_didok_place('destination', call_number)
            if o_didok != d_didok:
                break

    if rt in ('TR', 'TRIAS2020TR', 'J-S-TRIPSOD') and parameter_true('use_via'):
        while True:
            v_name, v_didok, v_coords = select_didok_place('via', call_number)
            if v_didok != o_didok and v_didok != d_didok:
                break

    result = [rt, o_name, o_didok, rnd(o_coords[0]), rnd(o_coords[1]),
              d_name, d_didok, rnd(d_coords[0]), rnd(d_coords[1]),
              v_name, v_didok, rnd(v_coords[0]), rnd(v_coords[1]),
              arrdeptime]

    # find the right template, depending on request type and mode (geo position or stop place ref or none):
    place_spec = ''
    if rt in ('TR', 'SER'):
        place_spec = '_geopos' if parameter_true('use_geopos') else '_stopplaceref'
    request = Template(rt + place_spec + '.')  # add dot to avoid ambiguity.

    # replace placeholders by given values:
    if rt in ('TR', 'SER', 'TRIAS2020TR', 'J-S-TRIPSOD'):
        request.replace('arrdep', arrdeptime)
        request.replace('arrdep_date', arrdeptime[0:10])
        request.replace('arrdep_time', arrdeptime[11:16])
        request.replace('o_name', 'ORIGIN' if parameter_true('mask_location_name') else o_name)
        request.replace('o_didok', o_didok)
        request.replace('o_x', rnd(o_coords[0]))
        request.replace('o_y', rnd(o_coords[1]))
        request.replace('d_name', 'DESTINATION' if parameter_true('mask_location_name') else d_name)
        request.replace('d_didok', d_didok)
        request.replace('d_x', rnd(d_coords[0]))
        request.replace('d_y', rnd(d_coords[1]))

    if rt in ('TR', 'TRIAS2020TR', 'J-S-TRIPSOD'):
        optional_via = ''
        if parameter_true('use_via') and v_didok != NA:
            optional_via = Template(rt + '_via')
            optional_via.replace('v_name', 'DESTINATION' if parameter_true('mask_location_name') else v_name)
            optional_via.replace('v_didok', v_didok)
        request.replace('via', optional_via)

    if rt == 'LIR':
        request.replace('location_name', o_name)

    if rt == 'TIR':
        # do an extra, prior call of TR to get journey-ref:
        prior_request = Template('TR_stopplaceref')
        prior_request.replace('via', '')
        prior_request.replace('timestamp', datetime.utcnow().isoformat() + 'Z')
        prior_request.replace('o_didok', o_didok)
        prior_request.replace('o_name', 'ORIGIN' if parameter_true('mask_location_name') else o_name)
        prior_request.replace('d_didok', d_didok)
        prior_request.replace('d_name', 'DESTINATION' if parameter_true('mask_location_name') else d_name)
        prior_request.replace('arrdep', arrdeptime)
        prior_request.replace('tr_number_of_results', '1')
        prior_request.replace('tr_include_track_sections', 'false')
        prior_request.replace('tr_include_turn_description', 'false')
        prior_request.replace('tr_include_intermediate_stops', 'false')
        prior_request.replace('tr_include_leg_projection', 'false')
        prior_response, prior_calc_time = http_post(session, env, str(prior_request))

        prior_resp_text = prior_response.content.decode('utf-8')
        op_day_ref = find_xml_element(prior_resp_text, '<ojp:OperatingDayRef>')
        journey_ref = find_xml_element(prior_resp_text, '<ojp:JourneyRef>')
        logging.info(f"- {call_number:04d}, {env:10s}, prior TR    ,"
                     f" from {o_name[0:15]:15s} to {d_name[0:15]:15s} via n/a            ,"
                     f" {round(1000*prior_calc_time):>6d} ms, {len(prior_response.content):>7d} bytes,"
                     f" {prior_response.status_code} {prior_response.reason}:"
                     f" op_day_ref={op_day_ref}, journey_ref={journey_ref}.")
        if not (op_day_ref and journey_ref):
            logging.info('-  ... op_day_ref and/or journey_ref are invalid - repeat.')
            return result, None

        if parameter_true('save_details'):
            save_file(test_directory, f"{env}_TIR_{call_number:04d}_prior_TR_request.xml", prior_request)
            save_file(test_directory,
                      f"{env:s}_TIR_{call_number:04d}_prior_TR_response_{prior_response.status_code}.xml",
                      pretty_print_xml(prior_resp_text))
        request.replace('journey_ref', journey_ref)
        request.replace('op_day_ref', op_day_ref)

    request.replace('timestamp', datetime.utcnow().isoformat() + 'Z')

    # 'use_params' if True, several parameters are set and slow down the system
    apply_params_and_restrictions(request)

    if parameter_true('save_details'):
        is_json = str(request).strip().startswith('{')
        ending = 'json' if is_json else 'xml'
        save_file(test_directory, f"{env}_{rt}_{call_number:04d}_request.{ending}", request)
    return result, str(request)


def http_post(session: requests.Session, env, body):
    bearer_token = 'Bearer ' + config.ENVIRONMENTS[env]['authBearerKey']
    service_url = config.ENVIRONMENTS[env]['apiEndpoint']

    # an improvement for better performance. Credits: Diogo Ferreira, Mentz
    request_provider = session if parameter_true('use_session') else requests
    content_type = 'json' if body.strip().startswith('{') else 'xml'
    headers = {"Authorization": bearer_token, "Content-Type": f"application/{content_type}; charset=utf-8"}
    body_utf8 = body.encode('utf-8')

    start_timestamp = time.time()
    response = request_provider.post(service_url, headers=headers, data=body_utf8)
    end_timestamp = time.time()
    calc_time = end_timestamp - start_timestamp

    return response, calc_time


def send_request(env, request_type, results_table, session: requests.Session, test_directory, call_number):
    retries, res, body = 10, None, None
    while retries > 0:
        res, body = build_request(env, session, request_type, test_directory, call_number)
        if body:
            break

        logging.info(f"- {call_number:04d}, {env:10s}, {request_type:12s}, build request failed, retry needed.")
        retries = retries - 1

    if body is None:
        logging.warning(f"- {call_number:04d}, {env:10s}, {request_type:12s}, failed to obtain a valid body.")
        return -1
    else:
        response, calc_time = http_post(session, env, body)
        resp_text = response.content.decode('utf-8')
        n_bytes = len(response.content)
        code_n_reason = str(response.status_code) + ' ' + str(response.reason)
        if response.status_code != 200:
            code_n_reason += ' / DATA ERROR!'
        elif 'ServiceDelivery' not in str(resp_text) and "trips" not in str(resp_text):
            code_n_reason += ' / NO <ServiceDelivery>/"trips" IN ANSWER!'

        res = [call_number, env] + res + [rnd(calc_time), n_bytes, code_n_reason]
        results_table.append(res)

        if parameter_true('save_details'):
            is_json = resp_text.strip().startswith('{')
            text = pretty_print_json(resp_text) if is_json else pretty_print_xml(resp_text)
            ending = 'json' if is_json else 'xml'
            save_file(test_directory, f"{env}_{request_type}_{call_number:04d}_response_{response.status_code}.{ending}", text)

        ori, des, via = res[3][0:15], res[7][0:15], res[11][0:15]
        logging.info(f"- {call_number:04d}, {env:10s}, {request_type:12s}, from {ori:15s} to {des:15s} via {via:15s},"
                     f" {round(1000*calc_time):>6d} ms, {len(response.content):>7d} bytes, {code_n_reason:s}.")

    return calc_time


def save_file(test_directory, file_name, text: str):
    joinnees = (config.OUTPUT, test_directory, file_name) if test_directory else (config.OUTPUT, file_name)
    file_path = os.path.join(*joinnees)
    with open(file=file_path, mode="w", encoding='utf-8') as file:
        file.write(str(text))


def save_csv_file(test_directory, env, rt, results_table):
    path = os.path.join(config.OUTPUT, test_directory, env + "_" + rt + "_results_table.csv")
    with open(file=path, mode="w", newline="", encoding='utf-8') as file:
        writer = csv.writer(file, delimiter=";")
        for row in results_table:
            writer.writerow(row)


def test_run(test_directory: str, env: str, request_type: str, stats: list):
    n_calls = parameter('number_of_requests', int)
    logging.info(f"TESTS ON ENVIRONMENT '{env}', REQUEST TYPE '{request_type}', {n_calls} CALLS:")
    results_table = [csvheaders]
    session = requests.Session()
    for i in range(0, n_calls):
        send_request(env, request_type, results_table, session, test_directory, i + 1)
        time.sleep(parameter('sleep_time', float))
    compute_statistics(stats, results_table, env, request_type)
    save_csv_file(test_directory, env, request_type, results_table)


def calc_percentile(array, percentile):
    # credits: https://www.delftstack.com/howto/python/python-percentile/
    return sorted(array)[int(math.ceil((len(array) * percentile) / 100)) - 1]


def compute_statistics(stats, results_table, env, request_type):
    n = len(results_table) - 1
    ct200 = [row[16] for row in results_table if row[18].startswith('200')]
    n200 = len(ct200)
    ctmin, ctmax, ctavg, ctp50, ctp90, ctp95 = NA, NA, NA, NA, NA, NA
    if n200 > 0:
        ctavg = round(1000 * statistics.mean(ct200))
        ctmin = round(1000 * min(ct200))
        ctmax = round(1000 * max(ct200))
        ctp50 = round(1000 * calc_percentile(ct200, 50.0))
        ctp90 = round(1000 * calc_percentile(ct200, 90.0))
        ctp95 = round(1000 * calc_percentile(ct200, 95.0))

    stats.append({'env': env, 'rt': request_type, 'n200': n200, 'n': n, 'ctavg': ctavg, 'ctmin': ctmin,
                       'ctmax': ctmax, 'ctp50': ctp50, 'ctp90': ctp90, 'ctp95': ctp95})


def save_statistics(stats: list, test_directory: str):
    stat = 'Test Statistics'
    stat += '\nService                                      number of tests                                                   calc. time [ms]'
    stat += '\nenvironment  request type        total         ok     not_ok        min    average        p50        p90        p95        max'
    for e in stats:
        stat += f"\n{e['env']:12s} {e['rt']:14s} {e['n']:10d} {e['n200']:10d} {e['n'] - e['n200']:10d}"
        stat += f" {e['ctmin']:10d} {e['ctavg']:10d} {e['ctp50']:10d} {e['ctp90']:10d} {e['ctp95']:10d} {e['ctmax']:10d}" if \
            e['n200'] > 0 else '        n/a        n/a        n/a        n/a        n/a        n/a'
    logging.info('STATISTICS:\n' + stat)
    save_file(test_directory, '_statistics.txt', stat)
    save_file(None, 'latest_statistics.txt', stat)


def copy_log_file(test_directory):
    shutil.copy2(LOG_FILE, os.path.join(config.OUTPUT, test_directory, '_log.txt'))


def process():
    parameter_file = load_parameters()
    set_random_seed()
    prepare_directories()
    load_didok()
    load_connections_file()
    stats = []
    environments = [e.strip() for e in parameter('environments').split(',')]
    request_types = [rt.strip() for rt in parameter('request_types').split(',')]
    remove_old_test_directories()
    test_directory = create_test_directory(parameter_file)
    for environment in environments:
        for request_type in request_types:
            if request_type in config.ENVIRONMENTS[environment]["supported_requests"]:
                try:
                    test_run(test_directory, environment, request_type, stats)
                except Exception as e:
                    logging.warning(f"Test skipped because of error: {str(e)}")
    save_statistics(stats, test_directory)
    copy_log_file(test_directory)


if __name__ == '__main__':
    process()
