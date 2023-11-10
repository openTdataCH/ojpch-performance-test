# CONFIGURATION:
# - basic, constant configuration is done here
# - secrets, keys, and other local adaptation is done in the local_configuration.py file (which is not in github)
# - runtime parameters for test runs are done in ./input/parameter.txt files;
#     - instead of 'parameter.txt', a different name may be provided as command-line argument when starting the test.

# sub-directories and parameter file:
DATA = 'data'
TEMPLATES = 'templates'
INPUT = 'input'
INPUT_PARAMETERS_DEFAULT = 'parameters.txt'
OUTPUT = 'output'

# OJP service environments, each with a short name like "PROD":
ENVIRONMENTS = {
    "PROD": {
        "apiEndpoint": "https://api.opentransportdata.swiss/ojp2020",
        "authBearerKey": "... key can be obtained by registering at https://opentransportdata.swiss/de/ ...",
        "supported_requests": {"TR", "TIR", "LIR", "SER"}
    },
    "TRIAS2020": {
        "apiEndpoint": "https://api.opentransportdata.swiss/trias2020",
        "authBearerKey": "...",
        "supported_requests": {"TRIAS2020TR"}
    }
}

# URL of the DIDOK data file (list of stations/stops in Swiss public transport)
DIDOK_PERMALINK = "https://opentransportdata.swiss/en/dataset/didok/resource_permalink/verkehrspunktelemente_actualdate.csv"
DIDOK_FILE = "verkehrspunktelemente_actualdate.csv"

# lookup file for didok codes of named places:
DIDOK_FOR_PLACES = "didok_for_places.json"


# if there exists a local_configuration, it is used and may supersede some of the above constants.
try:
    from local_configuration import *
except:
    pass