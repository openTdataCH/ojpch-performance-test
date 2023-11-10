"""Provides a helper class OAuth2Helper for obtainining an
OAuth2 access token from an OAuth2 authorization server,
based on OAuth2 client credentials flow (using client id and secret).

"""


import urllib3
import json
import requests


class OAuth2Helper:

    # Credits: https://developer.byu.edu/docs/consume-api/use-api/oauth-20/oauth-20-python-sample-code

    def __init__(self, url_token, client_id, client_secret, scope):
        urllib3.disable_warnings()
        self.url_token = url_token
        self.scope = scope
        self.client_id = client_id
        self.client_secret = client_secret
        self.current_token = None

    def get_token(self, new_token=False):
        if new_token or not self.current_token:
            data = {'grant_type': 'client_credentials', 'scope': self.scope}
            access_token_response = requests.post(self.url_token, data=data, verify=False, allow_redirects=False,
                                                  auth=(self.client_id, self.client_secret))
            self.current_token = json.loads(access_token_response.text)
        return self.current_token['access_token']

