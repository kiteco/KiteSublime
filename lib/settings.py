import sublime

_BASE_NAME = 'KiteSublime.sublime-settings'
_SETTINGS = None

def get(name, default=None):
    if _SETTINGS is None:
        _init_settings()
    return _SETTINGS.get(name, default)

def set(name, value):
    if _SETTINGS is None:
        _init_settings()
    if value is None:
        erase(name)
    else:
        _SETTINGS.set(name, value)
        sublime.save_settings(_BASE_NAME)

def erase(name):
    if _SETTINGS is None:
        _init_settings()
    _SETTINGS.erase(name)
    sublime.save_settings(_BASE_NAME)

def _init_settings():
    global _SETTINGS
    _SETTINGS = sublime.load_settings(_BASE_NAME)
