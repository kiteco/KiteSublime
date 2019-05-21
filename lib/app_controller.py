import sys

from ..lib import logger

if sys.platform == 'darwin':
    from ..lib.platform.darwin.app_controller import *
elif sys.platform == 'win32':
    from ..lib.platform.win32.app_controller import *
elif sys.platform in ('linux', 'linux2'):
    from ..lib.platform.linux.app_controller import *
else:
    from ..lib.platform.unsupported.app_controller import *

_KITE_INSTALLED = None
_KITE_APP = None


def is_kite_installed():
    if _KITE_INSTALLED is None:
        raise RuntimeError('Kite has not been located')

    return _KITE_INSTALLED


def launch_kite():
    if not is_kite_installed():
        raise RuntimeError('Kite is not installed')

    _launch_kite(_KITE_APP)


def launch_kite_if_not_running():
    if not is_kite_running():
        _launch_kite(_KITE_APP)


def locate_kite():
    global _KITE_INSTALLED, _KITE_APP
    _KITE_INSTALLED, _KITE_APP = _locate_kite()


def is_kite_running():
    return _is_kite_running()
