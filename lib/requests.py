import json
from http.client import CannotSendRequest, HTTPConnection

_KITED_HOST = 'localhost'
_KITED_PORT = 46624
_conn = None


def kited_get(path):
    if _conn is None:
        _init_connection()

    try:
        _conn.request('GET', path, headers={'Connection': 'keep-alive'})
    except (ConnectionRefusedError, CannotSendRequest) as ex:
        _reset_connection()
        raise ex
    else:
        resp = _conn.getresponse()
        body = resp.read()
        return resp, body

def kited_post(path, data=None):
    if _conn is None:
        _init_connection()

    try:
        _conn.request('POST', path, headers={'Connection': 'keep-alive'},
                      body=(json.dumps(data) if data is not None else None))
    except (ConnectionRefusedError, CannotSendRequest) as ex:
        _reset_connection()
        raise ex
    else:
        resp = _conn.getresponse()
        body = resp.read()
        return resp, body


def _init_connection():
    global _conn
    _conn = HTTPConnection(_KITED_HOST, port=_KITED_PORT, timeout=0.25)

def _reset_connection():
    global _conn
    _conn.close()
    _conn = None
