from typing import Dict
import urllib.parse
from requests.models import PreparedRequest


def get_authorized_url(url: str, username: str = None, password: str = None):
    if username is None and password is None:
        return url
    assert(
        url.startswith('http://') or url.startswith('https://')
    ), "Expected the url to start with http:// or https://"
    encoded_username = ""
    encoded_password = ""
    if username:
        encoded_username = urllib.parse.quote(username, safe='')
    if password:
        encoded_password = urllib.parse.quote(password, safe='')
    auth_part = f"{encoded_username}:{encoded_password}@"
    url_parts = url.partition('://')
    return url_parts[0] + url_parts[1] + auth_part + url_parts[2]


def add_parameters_to_url(url: str, parameters: Dict) -> str:
    req = PreparedRequest()
    req.prepare_url(url, parameters)
    return req.url
