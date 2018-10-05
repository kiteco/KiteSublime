import sublime

import json
import sys

from ..lib.reporter import send_rollbar_exc

_PATH = 'Packages/KiteSublime/Default.sublime-keymap'
_KEYMAP = None

def get(command):
    if _KEYMAP is None:
        _init_keymap()
    return _KEYMAP.get(command)

def _init_keymap():
    global _KEYMAP
    try:
        data = json.loads(sublime.load_resource(_PATH))
        _KEYMAP = {item['command']: item['keys'] for item in data}
    except ValueError:
        send_rollbar_exc(sys.exc_info())
        _KEYMAP = {}
