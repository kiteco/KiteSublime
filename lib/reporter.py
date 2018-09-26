import os
import rollbar

_ROLLBAR_IS_INIT = False

_ROLLBAR_TOKENS = {
    'dev': '7fa5ad5f027f4e0a887347441793c3ee',
    'prod': None,
}

def send_rollbar_msg(msg):
    if not _ROLLBAR_IS_INIT:
        _init_rollbar()
    rollbar.report_message(msg)

def _init_rollbar():
    token = (_ROLLBAR_TOKENS['prod'] if not os.getenv('SUBLIME_DEV')
             else _ROLLBAR_TOKENS['dev'])
    rollbar.init(token)
    _ROLLBAR_IS_INIT = True
