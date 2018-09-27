import os
import rollbar

from ..setup import is_development

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

def _init_rollbar():
    token = (_ROLLBAR_TOKENS['prod'] if not is_development()
             else _ROLLBAR_TOKENS['dev'])
    rollbar.init(token)
    _ROLLBAR_IS_INIT = True
