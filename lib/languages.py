from ..lib.errors import ExpectedError

class Languages:
    JAVASCRIPT = "JavaScript"
    GO = "Go"
    PYTHON = "Python"

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
    RB = ".rb"
    SH = ".sh"
    PHP = ".php"

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
        Extensions.RB,
        Extensions.SH,
        Extensions.PHP
])
