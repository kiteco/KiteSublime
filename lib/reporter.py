import sublime

import os
import rollbar
import sys
import traceback

from ..lib import logger, settings
from ..setup import is_development, is_same_package, package_version


_CAN_REPORT = None

_MODULE_NAME = None

_excepthook = None

_ROLLBAR_IS_INIT = False

_ROLLBAR_TOKENS = {
    'dev': '7fa5ad5f027f4e0a887347441793c3ee',
    'prod': '7c2c5c6b481c4672be08a30f83792647',
}


def check_reporting_enabled():
    global _CAN_REPORT

    if not settings.exists('report_errors'):
        ok = sublime.ok_cancel_dialog(
            '[Kite] Would you like to enable error reporting for Kite?\n\n' +
            'Error reporting allows us to find and fix issues with Kite\'s ' +
            'Sublime plugin so that we can improve your experience with it.\n'
        )
        settings.set('report_errors', ok or False)

    _CAN_REPORT = settings.get('report_errors')
    return _CAN_REPORT


def send_rollbar_msg(msg):
    if not _CAN_REPORT:
        return

    if not _ROLLBAR_IS_INIT:
        _init_rollbar()

    rollbar.report_message(msg, extra_data={
        'sublime_version': sublime.version(),
        'package_version': package_version(),
    })


def send_rollbar_exc(exc):
    if not _CAN_REPORT:
        return

    if not _ROLLBAR_IS_INIT:
        _init_rollbar()

    rollbar.report_exc_info(exc, extra_data={
        'sublime_version': sublime.version(),
        'package_version': package_version(),
    })


def setup_excepthook():
    if not _CAN_REPORT:
        return

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
