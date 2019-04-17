import json
import random
import socket
from http.client import CannotSendRequest, HTTPConnection
from threading import Lock

from ..lib import settings
from ..lib.errors import ExpectedError

_KITED_HOST = 'localhost'
_KITED_PORT = 46624

_conns = [None]*4
_locks = [Lock() for _ in range(4)]

_IGNORE_EXCEPTIONS = (
    socket.timeout,
)

_RESET_EXCEPTIONS = (
    ConnectionRefusedError,
    ConnectionResetError,
    OSError,
    CannotSendRequest,
)

def kited_get(path):
    """Makes a GET request to a Kite endpoint specified by the `path`
    argument. Returns the response and response body as a tuple.
    """
    conn, lock, idx = _get_connection()

    try:
        conn.request('GET', path, headers={'Connection': 'keep-alive'})
        resp = conn.getresponse()
        body = resp.read()
    except _IGNORE_EXCEPTIONS as exc:
        raise ExpectedError(exc, str(exc))
    except _RESET_EXCEPTIONS as exc:
        _reset_connection(idx)
        raise ExpectedError(exc, str(exc))
    else:
        return resp, body
    finally:
        lock.release()


def kited_post(path, data=None):
    """Makes a POST request to a Kite endpoint specified by the `path`
    argument. The `data` argument is JSON-serialized and used as the request
    body. Returns the response and response body as a tuple.
    """
    conn, lock, idx = _get_connection()

    try:
        conn.request('POST', path, headers={'Connection': 'keep-alive'},
                     body=(json.dumps(data) if data is not None else None))
        resp = conn.getresponse()
        body = resp.read()
    except _IGNORE_EXCEPTIONS as exc:
        raise ExpectedError(exc, str(exc))
    except _RESET_EXCEPTIONS as exc:
        _reset_connection(idx)
        raise ExpectedError(exc, str(exc))
    else:
        return resp, body
    finally:
        lock.release()


def _acquire_lock():
    idx = -1
    lock = None
    check = False
    while not check:
        idx = random.randint(0, len(_locks)-1)
        lock = _locks[idx]
        check = lock.acquire(False)
    return lock, idx


def _get_connection():
    lock, idx = _acquire_lock()
    if _conns[idx] is None:
        _init_connection(idx)
    return _conns[idx], lock, idx


def _init_connection(idx):
    global _conns

    timeout = settings.get('engine_timeout', 200)
    try:
        timeout = float(timeout) / 1000
    except ValueError:
        timeout = 0.2

    _conns[idx] = HTTPConnection(_KITED_HOST,
                                 port=_KITED_PORT,
                                 timeout=timeout)


def _reset_connection(idx):
    global _conns
    _conns[idx].close()
    _conns[idx] = None
