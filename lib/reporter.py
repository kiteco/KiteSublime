import sublime

import os
import rollbar
import sys
import traceback

from ..lib import logger
from ..setup import is_development, is_same_package, package_version


_MODULE_NAME = None

_excepthook = None

_ROLLBAR_IS_INIT = False

_ROLLBAR_TOKENS = {
    'dev': '7fa5ad5f027f4e0a887347441793c3ee',
    'prod': '790cab51b6c54f50bce651d28a22fc5a',
}


def send_rollbar_msg(msg):
    if not _ROLLBAR_IS_INIT:
        _init_rollbar()

    rollbar.report_message(msg, extra_data={
        'sublime_version': sublime.version(),
        'package_version': package_version(),
    })


def send_rollbar_exc(exc):
    if not _ROLLBAR_IS_INIT:
        _init_rollbar()

    rollbar.report_exc_info(exc, extra_data={
        'sublime_version': sublime.version(),
        'package_version': package_version(),
    })


def setup_excepthook():
    global _MODULE_NAME, _excepthook
    _MODULE_NAME = __name__.split('.')[0]

    if _excepthook is None:
        _excepthook = sys.excepthook
        sys.excepthook = _handle_exc


def release_excepthook():
    global _MODULE_NAME, _excepthook
    _MODULE_NAME = None

    if _excepthook is not None:
        sys.excepthook = _excepthook
        _excepthook = None


def _handle_exc(exctype, value, tb):
    exc = (exctype, value, tb)
    ss = traceback.extract_tb(tb)

    if len(ss) > 0 and is_same_package(ss[-1][0]):
        sublime.set_timeout_async(lambda: send_rollbar_exc(exc), 0)

    _excepthook(exctype, value, tb)


def _init_rollbar():
    global _ROLLBAR_IS_INIT

    token = (_ROLLBAR_TOKENS['prod'] if not is_development()
             else _ROLLBAR_TOKENS['dev'])

    rollbar.init(token)
    _ROLLBAR_IS_INIT = True
