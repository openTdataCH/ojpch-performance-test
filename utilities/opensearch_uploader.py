"""A module to provide upload to an OpenSearch index.

Credits: SBB AI Chat (GPT-4)
"""

import json

import requests

import configuration as config
from utilities import logging_wrapper as logging
from utilities import object_store as store


def upload_stats_to_opensearch():
    try:
        for stat in store.fetch("stats"):
            stat4os = {
                "time": stat["timestamp"],
                "environment": stat["environment"],
                "request": stat["request"],
                "use_parameters": str(stat["use_parameters"]),
                "ok": stat["n200"],
                "not_ok": stat["n"] - stat["n200"],
                "p50": stat["ctp50"],
                "p90": stat["ctp90"],
                "average": stat["ctavg"]
            }
            upload_data_to_opensearch(stat4os)

        logging.info(f"OpenSearch: {len(store.fetch('stats'))} tests stat JSONs uploaded to {config.OPENSEARCH['name']}.")
    except Exception as e:
        logging.info(f"upload_stats_to_opensearch() fails, no working config currently: {str(e)}:")


def upload_data_to_opensearch(data):
    headers = {"Content-Type": "application/json"}
    response = requests.post(
        f"{config.OPENSEARCH['url']}/{config.OPENSEARCH['index']}/_doc/",
        headers=headers,
        data=json.dumps(data, indent=2, ensure_ascii=False, sort_keys=False),
        auth=(config.OPENSEARCH['username'], config.OPENSEARCH['password'])
    )

    if response.status_code >= 300:
        logging.warning(f"upload_data_to_opensearch(): FAILED upload: {response.status_code} {response.reason}")
