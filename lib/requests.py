import json
from http.client import HTTPConnection

from ..lib import logger

_KITED_HOST = 'localhost'
_KITED_PORT = 46624
_conn = None

def kited_post(path, data=None):
    if _conn is None:
        _init_connection()
    _conn.request('POST', path, headers={'Connection': 'keep-alive'},
                  body=(json.dumps(data) if data is not None else None))
    resp = _conn.getresponse()
    body = resp.read()
    return resp, body

def _init_connection():
    global _conn
    _conn = HTTPConnection(_KITED_HOST, port=_KITED_PORT)
