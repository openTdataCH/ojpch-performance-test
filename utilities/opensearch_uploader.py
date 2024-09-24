"""A module to provide upload to an OpenSearch index.

Credits: SBB AI Chat (GPT-4)
"""

import json

import requests

import configuration as config
from utilities import logging_wrapper as logging
from utilities import object_store as store


def upload_stats_to_opensearch():
    successful = 0
    try:
        for stat in store.fetch("stats"):
            stat4os = {
                "time": stat["timestamp"],
                "environment": stat["environment"],
                "request": stat["request"],
                "use_parameters": str(stat["use_parameters"]).lower(),
                "ok": stat["n200"],
                "not_ok": stat["n"] - stat["n200"],
                "p50": stat["ctp50"],
                "p90": stat["ctp90"],
                "average": stat["ctavg"]
            }
            status_code, reason = upload_data_to_opensearch(stat4os)
            if status_code < 300:
                successful += 1
            elif status_code == 400:
                logging.warning(f"OpenSearch returns 400 Bad Request:\n{stat4os}")
            else:
                logging.warning(f"OpenSearch returns {status_code} {reason}.")

        n_tests = len(store.fetch('stats'))
        if successful == n_tests:
            logging.info(f"OpenSearch: all {n_tests} tests successfully uploaded to {config.OPENSEARCH['name']}.")
        else:
            logging.warning(f"OpenSearch: {n_tests-successful} uploads FAILED, {successful} successful on {config.OPENSEARCH['name']}.")
    except Exception as e:
        logging.warning(f"upload_stats_to_opensearch() fails, no working config currently: {str(e)}:")


def upload_data_to_opensearch(data):
    headers = {"Content-Type": "application/json"}
    response = requests.post(
        f"{config.OPENSEARCH['url']}/{config.OPENSEARCH['index']}/_doc/",
        headers=headers,
        data=json.dumps(data, indent=2, ensure_ascii=False, sort_keys=False),
        auth=(config.OPENSEARCH['username'], config.OPENSEARCH['password'])
    )
    return response.status_code, response.reason


