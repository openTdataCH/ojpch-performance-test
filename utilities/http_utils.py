"""Utility functions for http calls.

"""

import time

import requests

import configuration as config
from utilities import object_store as store
from utilities.parameters import param_true


def http_post(env, body):
    if param_true('use_session'):
        if store.fetch("session") is None:
            store.put("session", requests.Session())
        session: requests.Session = store.fetch("session")

    bearer_token = 'Bearer ' + config.ENVIRONMENTS[env]['authBearerKey']
    service_url = config.ENVIRONMENTS[env]['apiEndpoint']

    # an improvement for better performance. Credits: Diogo Ferreira, Mentz
    request_provider = session if param_true('use_session') else requests

    content_type = 'json' if body.strip().startswith('{') else 'xml'
    headers = {"Authorization": bearer_token, "Content-Type": f"application/{content_type}; charset=utf-8"}
    body_utf8 = body.encode('utf-8')

    start_timestamp = time.time()
    response = request_provider.post(service_url, headers=headers, data=body_utf8)
    end_timestamp = time.time()
    calc_time = end_timestamp - start_timestamp

    return response, calc_time
