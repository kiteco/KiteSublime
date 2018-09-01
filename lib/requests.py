import json
import random
from http.client import CannotSendRequest, HTTPConnection

_KITED_HOST = 'localhost'
_KITED_PORT = 46624
_conns = [None]*4


def kited_get(path):
    conn, idx = _get_connection()

    try:
        conn.request('GET', path, headers={'Connection': 'keep-alive'})
    except (ConnectionRefusedError, CannotSendRequest) as ex:
        _reset_connection(idx)
        raise ex
    else:
        resp = conn.getresponse()
        body = resp.read()
        return resp, body

def kited_post(path, data=None):
    conn, idx = _get_connection()

    try:
        conn.request('POST', path, headers={'Connection': 'keep-alive'},
                     body=(json.dumps(data) if data is not None else None))
    except (ConnectionRefusedError, CannotSendRequest) as ex:
        _reset_connection(idx)
        raise ex
    else:
        resp = conn.getresponse()
        body = resp.read()
        return resp, body


def _get_connection():
    idx = random.randint(0, 3)
    if _conns[idx] is None:
        _init_connection(idx)
    return _conns[idx], idx

def _init_connection(idx):
    global _conns
    _conns[idx] = HTTPConnection(_KITED_HOST, port=_KITED_PORT, timeout=0.25)

def _reset_connection(idx):
    global _conns
    _conns[idx].close()
    _conns[idx] = None
