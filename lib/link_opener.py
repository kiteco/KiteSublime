import sys

if sys.platform == 'darwin':
    from ..lib.platform.darwin.link_opener import *
elif sys.platform == 'win32':
    from ..lib.platform.win32.link_opener import *
else:
    from ..lib.platform.unsupported.link_opener import *

def open_browser(ident):
    return _open_browser(ident)

def open_copilot(ident):
    return _open_copilot(ident)
