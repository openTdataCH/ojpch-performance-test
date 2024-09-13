"""Module for building a valid request body

"""

import math
import random
from datetime import datetime, timedelta, date

from utilities import logging_wrapper as logging
from utilities import object_store as store
from utilities import stop_points
from utilities.datetime_utils import sleep_to_avoid_quota_exceeding, utc_now_iso
from utilities.file_utils import save_file
from utilities.http_utils import http_post
from utilities.math_utils import rnd
from utilities.parameters import param, param_true
from utilities.statistics_utils import NA
from utilities.string_utils import find_xml_element
from utilities.string_utils import pretty_print_xml
from utilities.template_util import Template


def build_request(call_number: int) -> (list, str):
    """Build a request for the given type, with random parameters filled-in;
    if not successfull (in case of a TIR), return "None"."""
    env, rt = store.fetch("environment"), store.fetch("request_type")
    d_name, d_didok, d_coords = NA, NA, (0.0, 0.0)
    v_name, v_didok, v_coords = NA, NA, (0.0, 0.0)

    arrdeptime = select_date_time_at_random() if rt in ('TR10', 'TR20', 'SER10', 'SER20', 'TIR10', 'TIR20', 'TRIAS2020TR', 'J-S-TRIPSOD') else NA

    # choose random origin (and destination for TR) from didok:
    o_name, o_didok, o_coords = select_stop_point('origin', call_number)
    if rt in ('TR10', 'TR20', 'TIR10', 'TIR20', 'TRIAS2020TR', 'J-S-TRIPSOD'):
        while True:
            d_name, d_didok, d_coords = select_stop_point('destination', call_number)
            if o_didok != d_didok:
                break

    if rt in ('TR10', 'TR20', 'TRIAS2020TR', 'J-S-TRIPSOD') and param_true('use_via'):
        while True:
            v_name, v_didok, v_coords = select_stop_point('via', call_number)
            if v_didok != o_didok and v_didok != d_didok:
                break

    result = [rt, o_name, o_didok, rnd(o_coords[0]), rnd(o_coords[1]),
              d_name, d_didok, rnd(d_coords[0]), rnd(d_coords[1]),
              v_name, v_didok, rnd(v_coords[0]), rnd(v_coords[1]),
              arrdeptime]

    # find the right template, depending on request type and mode (geo position or stop place ref or none):
    place_spec = ''
    if rt in ('TR10', 'TR20', 'SER10', 'SER20', 'LIR10', 'LIR20'):
        place_spec = '_geopos' if param_true('use_geopos') else '_stopplaceref'
    request = Template(rt + place_spec + '.')  # add dot to avoid ambiguity.

    # replace placeholders by given values:
    if rt in ('TR10', 'TR20', 'SER10', 'SER20', 'TRIAS2020TR', 'J-S-TRIPSOD'):
        request.replace('arrdep', arrdeptime)
        request.replace('arrdep_date', arrdeptime[0:10])
        request.replace('arrdep_time', arrdeptime[11:16])
        request.replace('o_name', 'ORIGIN' if param_true('mask_location_name') else o_name)
        request.replace('o_didok', o_didok)
        request.replace('o_x', rnd(o_coords[0]))
        request.replace('o_y', rnd(o_coords[1]))
        request.replace('d_name', 'DESTINATION' if param_true('mask_location_name') else d_name)
        request.replace('d_didok', d_didok)
        request.replace('d_x', rnd(d_coords[0]))
        request.replace('d_y', rnd(d_coords[1]))

    if rt in ('TR10', 'TR20', 'TRIAS2020TR', 'J-S-TRIPSOD'):
        optional_via = ''
        if param_true('use_via') and v_didok != NA:
            optional_via = Template(rt + '_via')
            optional_via.replace('v_name', 'DESTINATION' if param_true('mask_location_name') else v_name)
            optional_via.replace('v_didok', v_didok)
        request.replace('via', optional_via)

    if rt in ('LIR10', 'LIR20'):
        request.replace('location_name', o_name)
        request.replace('o_x', rnd(o_coords[0]))
        request.replace('o_y', rnd(o_coords[1]))

    if rt in ('TIR10', 'TIR20'):
        # do an extra, prior call of TR to get journey-ref:
        ojp_vers = rt[3:5]
        prior_request = Template(f'TR{ojp_vers}_stopplaceref')
        prior_request.replace('via', '')
        prior_request.replace('timestamp', utc_now_iso())
        prior_request.replace('o_didok', o_didok)
        prior_request.replace('o_name', 'ORIGIN' if param_true('mask_location_name') else o_name)
        prior_request.replace('d_didok', d_didok)
        prior_request.replace('d_name', 'DESTINATION' if param_true('mask_location_name') else d_name)
        prior_request.replace('arrdep', arrdeptime)
        prior_request.replace('tr_number_of_results', '1')
        prior_request.replace('tr_include_track_sections', 'false')
        prior_request.replace('tr_include_turn_description', 'false')
        prior_request.replace('tr_include_intermediate_stops', 'false')
        prior_request.replace('tr_include_leg_projection', 'false')
        prior_response, prior_calc_time = http_post(env, str(prior_request))
        sleep_to_avoid_quota_exceeding()

        prior_resp_text = prior_response.content.decode('utf-8')
        op_day_ref = find_xml_element(prior_resp_text, '<ojp:OperatingDayRef>' if ojp_vers == "10" else '<OperatingDayRef>')
        journey_ref = find_xml_element(prior_resp_text, '<ojp:JourneyRef>' if ojp_vers == "10" else '<JourneyRef>')
        logging.log1connection(nr=call_number, env=env, req=f"prior TR{ojp_vers}", a=o_name, b=d_name, via="",
                               ms=round(1000*prior_calc_time), bytes=len(prior_response.content),
                               code_n_reason=f"{prior_response.status_code} {prior_response.reason}",
                               message=f"op_day_ref={op_day_ref}, journey_ref={journey_ref}")
        if not (op_day_ref and journey_ref):
            logging.info('-  ... op_day_ref and/or journey_ref are invalid - repeat.')
            return result, None

        if param_true('save_details'):
            save_file(store.fetch("test_directory"), f"{env}_TIR_{call_number:04d}_prior_TR_request.xml", prior_request)
            save_file(store.fetch("test_directory"),
                      f"{env:s}_TIR_{call_number:04d}_prior_TR_response_{prior_response.status_code}.xml",
                      pretty_print_xml(prior_resp_text))
        request.replace('journey_ref', journey_ref)
        request.replace('op_day_ref', op_day_ref)

    request.replace('timestamp', utc_now_iso())

    # 'use_params' if True, several parameters are set and slow down the system
    apply_params_and_restrictions(request)

    if param_true('save_details'):
        is_json = str(request).strip().startswith('{')
        ending = 'json' if is_json else 'xml'
        plus = "+" if store.fetch("use_pars") else ""
        save_file(store.fetch("test_directory"), f"{env}_{rt}{plus}_{call_number:04d}_request.{ending}", request)
    return result, str(request)


def apply_params_and_restrictions(request: Template):
    # try to insert everything, regardless of the given request type - will be ignored if no placeholder in template:
    for par in ('tr_include_track_sections', 'tr_include_leg_projection', 'tr_include_turn_description',
                'tr_include_intermediate_stops', 'ser_operator_exclude', 'ser_operator_ref',
                'ser_include_previous_calls', 'ser_include_onward_calls', 'ser_include_realtime_data',
                'ser_include_realtime_data2.0',
                'lir_include_pt_modes', 'tir_include_calls', 'tir_include_track_sections', 'tir_include_service',
                'trias2020tr_include_track_sections', 'trias2020tr_include_leg_projection',
                'trias2020tr_include_intermediate_stops'):
        # Parameter is set to 'true' if main switch use_params=True AND par_xy=True:
        value = str(store.fetch("use_pars") and param_true(par)).lower()
        request.replace(par, value)

    # other, non-boolean OJP parameters:
    for par in ('ser_number_of_results', 'ser_stop_event_type_reference', 'ser_operator_exclude', 'ser_operator_ref',
                'lir_geo_restriction_type', 'lir_number_of_results', 'trias2020tr_number_of_results',
                'tr_number_of_results'):
        request.replace(par, param(par))


def select_date_time_at_random() -> str:
    """Select a random departure date/time, within the bounds given by the parameters."""
    days_ahead_min, days_ahead_max = param('days_ahead_min', int), param('days_ahead_max', int)
    hours_min, hours_max = param('hours_min', int), param('hours_max', int)
    minutes_min, minutes_max = param('minutes_min', int), param('minutes_max', int)

    days_ahead = random.randrange(days_ahead_min, days_ahead_max + 1)
    hours = random.randrange(hours_min, hours_max + 1)
    minutes = random.randrange(minutes_min, minutes_max + 1)

    date_ahead = date.today() + timedelta(days=days_ahead)
    return datetime(date_ahead.year, date_ahead.month, date_ahead.day, hours, minutes, 0).isoformat()


def add_random_offset_to_coord(coords_lon_lat: tuple, max_radius: float):
    """Randomly offset a point at a given coordinate by max_radius. Using uniform random distribution.
    Using an approximative formula which is ~ 1 % precise for Switzerland."""
    p = (1.0, 1.0)
    while math.sqrt(p[0] * p[0] + p[1] * p[1]) >= 1.0:  # find a random point within a circle of radius 1.0:
        p = (2.0 * random.random() - 1.0, 2.0 * random.random() - 1.0)
    return (coords_lon_lat[0] + max_radius * 0.01314 * p[0], coords_lon_lat[1] + max_radius * 0.00900 * p[1])


def select_stop_point(role: str, call_number: int) -> (str, int, tuple):
    """Select a stop point (name, number, coords) either randomly from the given stop points dict sp_dict,
    or from a connections file."""
    if param_true('use_connections_file'):
        connections = store.fetch("connections")
        conn = connections[(call_number - 1) % len(connections)]  # if call_number exceeds # connections, cycle around
        conn = conn + [None, None]  # to avoid out-of-bounds errors
        if conn[0] is None or conn[1] is None:
            raise ValueError("ERROR in connections file: connections must always contain a 'from' and a 'to' value!")
        if conn[0] == conn[1] or conn[0] == conn[2] or conn[1] == conn[2]:
            raise ValueError(f"ERROR in connections file: from={conn[0]}, to={conn[1]} and via={conn[2]} must be different!")
        place = conn[0] if role == 'origin' else conn[1] if role == 'destination' else conn[2]
        if place:
            sp = stop_points.get_by_name(place)
            if sp:
                return sp.name, sp.number, (sp.lon, sp.lat)
        return NA, NA, (0.0, 0.0)
    else:
        keys = stop_points.keys()
        sp = stop_points.get_by_name(keys[random.randrange(0, len(keys))])
        sp_coords = [sp.lon, sp.lat]
        if param_true('use_geopos'):
            sp_coords = add_random_offset_to_coord(sp_coords, param('max_dist_from_stop', float))
        return sp.name, sp.number, sp_coords


def request_type_w_or_wo_parameters_selector(request_type: str) -> (str, list):
    """Based on request_type, return a list, to run without, with, or both wo/w parameters."""
    if request_type.endswith("+"):
        return request_type[:-1], [True]
    if request_type.endswith("-"):
        return request_type[:-1], [False]
    if request_type.endswith("*"):
        return request_type[:-1], [False, True]
    return request_type, [False]


