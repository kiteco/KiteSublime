import sublime

import json
import re
import sys

from ..lib.reporter import send_rollbar_exc

_PATH = 'Packages/KiteSublime/Default.sublime-keymap'
_KEYMAP = None

def get(command):
    if _KEYMAP is None:
        _init_keymap()
    return _KEYMAP.get(command)

def keystr(keys):
    return ','.join(keys)

def _init_keymap():
    global _KEYMAP
    try:
        # Remove C-style comments from the `.sublime-keymap` file
        contents = sublime.load_resource(_PATH)
        contents = re.sub(r'\\\n', '', contents)
        contents = re.sub(r'//.*\n', '\n', contents)
        data = json.loads(contents)
        _KEYMAP = {item['command']: item['keys'] for item in data}
    except ValueError:
        send_rollbar_exc(sys.exc_info())
        _KEYMAP = {}
