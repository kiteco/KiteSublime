import json
from http.client import HTTPConnection

from ..lib import logger

_KITED_HOST = 'localhost'
_KITED_PORT = 46624

def kited_post(path, data=None):
    conn = HTTPConnection(_KITED_HOST, port=_KITED_PORT)
    conn.request('POST', path,
                 body=(json.dumps(data) if data is not None else None))
    resp = conn.getresponse()
    body = resp.read()
    conn.close()
    return resp, body
