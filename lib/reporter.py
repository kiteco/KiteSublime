import sublime

import os
import rollbar
import sys

from ..lib import logger
from ..setup import is_development


_MODULE_NAME = None

_excepthook = None

_ROLLBAR_IS_INIT = False

_ROLLBAR_TOKENS = {
    'dev': '7fa5ad5f027f4e0a887347441793c3ee',
    'prod': None,
}


def send_rollbar_msg(msg):
    if not _ROLLBAR_IS_INIT:
        _init_rollbar()
    rollbar.report_message(msg)


def send_rollbar_exc(exc):
    if not _ROLLBAR_IS_INIT:
        _init_rollbar()
    rollbar.report_exc_info(exc)


def setup_excepthook():
    global _MODULE_NAME, _excepthook
    _MODULE_NAME = __name__.split('.')[0]
    if _excepthook is None:
        _excepthook = sys.excepthook
        sys.excepthook = _handle_exc
        logger.log('setup exception hook')


def release_excepthook():
    global _MODULE_NAME, _excepthook
    _MODULE_NAME = None
    if _excepthook is not None:
        sys.excepthook = _excepthook
        _excepthook = None


def _handle_exc(exctype, value, tb):
    exc = (exctype, value, tb)
    sublime.set_timeout_async(lambda: send_rollbar_exc(exc), 0)
    _excepthook(exctype, value, tb)


def _init_rollbar():
    token = (_ROLLBAR_TOKENS['prod'] if not is_development()
             else _ROLLBAR_TOKENS['dev'])
    rollbar.init(token)
    _ROLLBAR_IS_INIT = True
