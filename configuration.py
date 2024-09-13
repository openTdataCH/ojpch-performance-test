"""Basic configuration file, which defines folders, URLs, API keys, etc. that remain constant for all tests.
Basic, constant configuration is done here.
The file (as loaded from github) contains some of the currently known system URLs, requests, etc.,
and some "reosonable" config of sub-directory names, default parameter name, etc.

In a local setup, this file may be complemented with a local_configuration.py module,
which supersedes some of the config values, especially secrets, etc.
local_configuration.py MUST NOT BE COMMITED to github.

Parameters for individual test series, finally, are set up in a "test_parameters" file.
"""

# sub-directories and parameter file:
FOLDERS = {
    "output": "output",
    "stop_points": "stop_points",
    "templates": 'templates',
    "test_parameters": "test_parameters",
}

# OJP service environments, each with a short name like "PROD":
ENVIRONMENTS = {
    "OJP20PROD": {
        "apiEndpoint": "https://api.opentransportdata.swiss/ojp20",
        "authBearerKey": "... key can be obtained by registering at https://opentransportdata.swiss/de/ ...",
        "supported_requests": {"TR20", "TIR20", "LIR20", "SER20"}
    },
    "OJP10PROD": {
        "apiEndpoint": "https://api.opentransportdata.swiss/ojp2020",
        "authBearerKey": "... key can be obtained by registering at https://opentransportdata.swiss/de/ ...",
        "supported_requests": {"TR10", "TIR10", "LIR10", "SER10"}
    },
    "TRIAS2020": {
        "apiEndpoint": "https://api.opentransportdata.swiss/trias2020",
        "authBearerKey": "...",
        "supported_requests": {"TRIAS2020TR"}
    }
}

# URL of the Service Points data file (list of stations/stops in Swiss public transport)
SP_PERMALINK = "https://opentransportdata.swiss/de/dataset/service-points-actual-date/permalink"

# if there exists a local_configuration, it is used and may supersede some of the above constants.
try:
    from local_configuration import *
except:
    pass