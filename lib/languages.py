from ..lib.errors import ExpectedError

class Languages:
    JAVASCRIPT = "JavaScript"
    GO = "Go"
    PYTHON = "Python"

class Extensions:
    PY = ".py"
    GO = ".go"
    JS = ".js"
    JSX = ".jsx"
    VUE = ".vue"

LEXICAL_EXTS = (Extensions.GO, Extensions.JS, Extensions.JSX, Extensions.VUE)

SUPPORTED_EXTS_TO_LANG = {
    Extensions.PY: Languages.PYTHON,
    Extensions.GO: Languages.GO,
    Extensions.JS: Languages.JAVASCRIPT,
    Extensions.JSX: Languages.JAVASCRIPT,
    Extensions.VUE: Languages.JAVASCRIPT,
}

_LANG_TO_ENABLED_PATH = {
    Languages.GO: "/clientapi/settings/kite_lexical_enabled",
    Languages.JAVASCRIPT: "/clientapi/settings/kite_js_enabled",
}

def ext_to_lang(ext):
    return SUPPORTED_EXTS_TO_LANG[ext]

