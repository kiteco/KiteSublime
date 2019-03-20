import sys

if sys.platform == 'darwin':
    from ..lib.platform.darwin.link_opener import *
elif sys.platform == 'win32':
    from ..lib.platform.win32.link_opener import *
elif sys.platform in ('linux', 'linux2'):
    from ..lib.platform.linux.link_opener import *
else:
    from ..lib.platform.unsupported.link_opener import *


def open_browser(ident):
    return _open_browser(ident)


def open_browser_url(url):
    return _open_browser_url(url)


def open_copilot(ident):
    return _open_copilot(ident)


def open_copilot_root(path):
    return _open_copilot_root(path)
