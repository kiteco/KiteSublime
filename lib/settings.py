import sublime

_BASE_NAME = 'KiteSublime.sublime-settings'
_SETTINGS = None
_GLOBAL_SETTINGS = None

def exists(name):
    if _SETTINGS is None:
        _init_settings()
    return _SETTINGS.has(name)

def exists_global(name):
    if _GLOBAL_SETTINGS is None:
        _init_settings()
    return _GLOBAL_SETTINGS.has(name)

def get(name, default=None):
    if _SETTINGS is None:
        _init_settings()
    return _SETTINGS.get(name, default)

def get_global(name):
    if _GLOBAL_SETTINGS is None:
        _init_settings()
    return _GLOBAL_SETTINGS.get(name)

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
    global _SETTINGS, _GLOBAL_SETTINGS
    _SETTINGS = sublime.load_settings(_BASE_NAME)
    _GLOBAL_SETTINGS = sublime.load_settings('Preferences.sublime-settings')
