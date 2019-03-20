import sys

if sys.platform == 'darwin':
    from ..lib.platform.darwin.file_system import *
elif sys.platform == 'win32':
    from ..lib.platform.win32.file_system import *
elif sys.platform in ('linux', 'linux2'):
    from ..lib.platform.linux.file_system import *
else:
    from ..lib.platform.unsupported.file_system import *


def path_for_url(path):
    return _path_for_url(path)
