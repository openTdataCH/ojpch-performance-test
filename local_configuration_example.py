"""
This file shows how the file 'local_configuration.py' may be set up.

Local configuration that will be imported at the end of configuration.py:
- includes secrets for API access.
- may include OAuth2 stuff to obtain a fresh bearer token for J-S PROD service.
"""


# configuration and OAuth2 token for Journey Service (J-S PROD service):
# https://developer.sbb.ch/apis/journey-service/documentation
from utilities.oauth_util import OAuth2Helper

J_S_URL_TOKEN = "... URL of the OAuth2 Authorization Server to obtain a token."
J_S_SCOPE = "... scope to obtain a token ..."
J_S_CLIENT_ID = "... client ID to obtain a token ..."
J_S_CLIENT_SECRET = "... client secret to obtain a token ..."
J_S_URL_API = "https://journey-service.api.sbb.ch:443/v3/trips/by-origin-destination"
oauth_helper = OAuth2Helper(url_token=J_S_URL_TOKEN, scope=J_S_SCOPE, client_id=J_S_CLIENT_ID,
                                client_secret=J_S_CLIENT_SECRET)
j_s_token = oauth_helper.get_token()


# environments - will supersede the variable in configuration.py:
ENVIRONMENTS = {
    "PROD": {
        "apiEndpoint": "https://api.opentransportdata.swiss/ojp2020",
        "authBearerKey": ".... ",
        "supported_requests": {"TR", "TIR", "LIR", "SER"}
    },
    "TRIAS2020": {
        "apiEndpoint": "https://api.opentransportdata.swiss/trias2020",
        "authBearerKey": "....",
        "supported_requests": {"TRIAS2020TR"}
    },
    "J-S-PROD": {
        "apiEndpoint": J_S_URL_API,
        "authBearerKey": j_s_token,
        "supported_requests": {"J-S-TRIPSOD"}
    }
}
