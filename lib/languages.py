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

SUPPORTED_EXTS_TO_LANG = {
    Extensions.PY: Languages.PYTHON,
    Extensions.GO: Languages.GO,
    Extensions.JS: Languages.JAVASCRIPT,
    Extensions.JSX: Languages.JAVASCRIPT,
    Extensions.VUE: Languages.JAVASCRIPT,
}

def ext_to_lang(ext):
    return SUPPORTED_EXTS_TO_LANG[ext]

