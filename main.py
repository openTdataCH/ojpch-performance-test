"""A python script to run performance tests of an OJP (Open API for distributed journey planning) API service.

See: https://github.com/openTdataCH/ojpch-performance-test

2023-11-08 ... 2024-09-03
Matthias Günter, Diogo Ferreira, Markus Meier, Thomas Odermatt
"""

import configuration as config
from utilities import logging_wrapper as logging
from utilities import object_store as store
from utilities import prepare
from utilities.datetime_utils import sleep_to_avoid_quota_exceeding
from utilities.file_utils import save_file
from utilities.http_utils import http_post
from utilities.math_utils import rnd
from utilities.opensearch_uploader import upload_stats_to_opensearch
from utilities.parameters import param, param_true
from utilities.request_builder import build_request, request_type_w_or_wo_parameters_selector
from utilities.statistics_utils import save_statistics, compute_statistics, save_results_table_csv_file, \
    new_results_table
from utilities.string_utils import pretty_print_xml, pretty_print_json


def send_request(call_number):
    env, rt = store.fetch("environment"), store.fetch("request_type")
    rt_plus = rt + "+" if store.fetch("use_pars") else rt
    retries, res, body = 10, None, None
    while retries > 0:
        res, body = build_request(call_number)
        if body:
            break

        logging.info(f"- {call_number:02d}, {env:10s}, {rt_plus:12s}, build request failed, retry needed.")
        retries = retries - 1

    if body is None:
        logging.warning(f"- {call_number:02d}, {env:10s}, {rt_plus:12s}, failed to obtain a valid body.")
        return -1
    else:
        response, calc_time = http_post(env, body)
        resp_text = response.content.decode('utf-8')
        n_bytes = len(response.content)
        code_n_reason = str(response.status_code) + ' ' + str(response.reason)
        if response.status_code != 200:
            code_n_reason += ' / DATA ERROR!'
        elif 'ServiceDelivery' not in str(resp_text) and "trips" not in str(resp_text):
            code_n_reason += ' / NO <ServiceDelivery>/"trips" IN ANSWER!'

        res = [call_number, env] + res + [rnd(calc_time), n_bytes, code_n_reason]
        store.fetch("results_table").append(res)

        if param_true('save_details'):
            is_json = resp_text.strip().startswith('{')
            text = pretty_print_json(resp_text) if is_json else pretty_print_xml(resp_text)
            plus = "+" if store.fetch("use_pars") else ""
            ending = 'json' if is_json else 'xml'
            save_file(store.fetch("test_directory"), f"{env}_{rt}{plus}_{call_number:04d}_response_{response.status_code}.{ending}", text)

        a, b, via = res[3], res[7], res[11]
        logging.log1connection(nr=call_number, env=env, req=rt_plus, a=a, b=b, via=via, ms=round(1000*calc_time),
                               bytes=len(response.content), code_n_reason=code_n_reason)
    return calc_time


def test_run():
    n_calls = param('number_of_requests', int)
    logging.info(f"""{n_calls} tests on {store.fetch("environment")} with {store.fetch("request_type")}"""
                 f""" with{'' if store.fetch("use_pars") else 'out'} parameters:""")
    store.put("results_table", new_results_table())
    for i in range(0, n_calls):
        send_request(i + 1)
        sleep_to_avoid_quota_exceeding()
    compute_statistics()
    save_results_table_csv_file()


def process():
    prepare.set_random_seed()
    prepare.prepare_directories()
    prepare.load_connections_file()
    store.put("stats", [])
    environments = [e.strip() for e in param('environments').split(',')]
    request_types = [rt.strip() for rt in param('request_types').split(',')]
    prepare.remove_old_test_directories()
    prepare.create_test_directory()
    for environment in environments:
        for request_type in request_types:
            rt, wo_w_pars = request_type_w_or_wo_parameters_selector(request_type)
            if rt in config.ENVIRONMENTS[environment]["supported_requests"]:
                for use_pars in wo_w_pars:
                    try:
                        store.put("environment", environment)
                        store.put("request_type", rt)
                        store.put("use_pars", use_pars)
                        test_run()
                    except Exception as e:
                        logging.warning(f"Test skipped because of error: {str(e)}")
    save_statistics()
    upload_stats_to_opensearch()
    logging.copy_log_file_to_test_directory()


if __name__ == '__main__':
    process()
