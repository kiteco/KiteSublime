from ..lib.errors import ExpectedError

class Languages:
    JAVASCRIPT = "JavaScript"
    GO = "Go"
    PYTHON = "Python"
    UNCATEGORIZED = "Uncategorized"

class Extensions:
    # Existing Models
    PY = ".py"
    GO = ".go"
    # Modern Web
    JS = ".js"
    JSX = ".jsx"
    VUE = ".vue"
    TS = ".ts"
    TSX = ".tsx"
    CSS = ".css"
    LESS = ".less"
    HTML = ".html"
    # C Styled
    C = ".c"
    CC = ".cc"
    CPP = ".cpp"
    CS = ".cs"
    H = ".h"
    HPP = ".hpp"
    M = ".m"
    # Java++
    SCALA = ".scala"
    JAVA = ".java"
    KT = ".kt"
    # Other
    PHP = ".php"
    RB = ".rb"
    SH = ".sh"

SUPPORTED_EXTS = set([
        Extensions.PY,
        Extensions.GO,
        Extensions.JS,
        Extensions.JSX,
        Extensions.VUE,
        Extensions.TS,
        Extensions.TSX,
        Extensions.CSS,
        Extensions.LESS,
        Extensions.HTML,
        Extensions.C,
        Extensions.CC,
        Extensions.CPP,
        Extensions.CS,
        Extensions.H,
        Extensions.HPP,
        Extensions.M,
        Extensions.SCALA,
        Extensions.JAVA,
        Extensions.KT,
        Extensions.PHP,
        Extensions.RB,
        Extensions.SH,
])

SUPPORTED_EXTS_TO_LANG = {
    # Existing Models
    Extensions.PY: Languages.PYTHON,
    Extensions.GO: Languages.GO,
    # Modern Web
    Extensions.JS: Languages.JAVASCRIPT,
    Extensions.JSX: Languages.JAVASCRIPT,
    Extensions.VUE: Languages.JAVASCRIPT,

    Extensions.TS: Languages.UNCATEGORIZED,
    Extensions.TSX: Languages.UNCATEGORIZED,
    Extensions.CSS: Languages.UNCATEGORIZED,
    Extensions.LESS: Languages.UNCATEGORIZED,
    Extensions.HTML: Languages.UNCATEGORIZED,
    # C Styled
    Extensions.C: Languages.UNCATEGORIZED,
    Extensions.CC: Languages.UNCATEGORIZED,
    Extensions.CPP: Languages.UNCATEGORIZED,
    Extensions.CS: Languages.UNCATEGORIZED,
    Extensions.H: Languages.UNCATEGORIZED,
    Extensions.HPP: Languages.UNCATEGORIZED,
    Extensions.M: Languages.UNCATEGORIZED,
    # Java++
    Extensions.SCALA: Languages.UNCATEGORIZED,
    Extensions.JAVA: Languages.UNCATEGORIZED,
    Extensions.KT: Languages.UNCATEGORIZED,
    # Other
    Extensions.PHP: Languages.UNCATEGORIZED,
    Extensions.RB: Languages.UNCATEGORIZED,
    Extensions.SH: Languages.UNCATEGORIZED,
}

def ext_to_lang(ext):
    return SUPPORTED_EXTS_TO_LANG[ext]

