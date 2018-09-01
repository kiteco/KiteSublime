import sublime

import json

_PATH = 'Packages/KPP/Default.sublime-keymap'
_KEYMAP = None

def get(command):
    if _KEYMAP is None:
        _init_keymap()
    return _KEYMAP.get(command)

def _init_keymap():
    global _KEYMAP
    data = json.loads(sublime.load_resource(_PATH))
    _KEYMAP = {item['command']: item['keys'] for item in data}
