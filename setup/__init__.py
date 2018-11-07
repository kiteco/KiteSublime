import os
import platform
import sublime
import subprocess
import sys

_ROOT = None
_DEVELOPMENT = False
_OS_VERSION = ''

def setup_all():
    global _DEVELOPMENT
    _setup_path()
    _setup_os_version()
    if os.path.exists(os.path.join(_ROOT, 'DEVELOPMENT')):
        os.environ['SUBLIME_DEV'] = '1'
        _DEVELOPMENT = True

def is_development():
    return _DEVELOPMENT

def is_same_package(filename):
    return filename.startswith(_ROOT)

def os_version():
    return _OS_VERSION

def _setup_path():
    global _ROOT
    _ROOT = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))

    # Determine if python-jinja2 package exists. If so, we need to modify the
    # path such that we get precedence.
    idx = -1
    for i, p in enumerate(sys.path):
        if 'python-jinja2' in p:
            idx = i
            break

    if idx != -1:
        sys.path.insert(idx, os.path.join(_ROOT, 'vendor'))
    else:
        sys.path.append(os.path.join(_ROOT, 'vendor'))

def _setup_os_version():
    global _OS_VERSION

    if sys.platform == 'darwin':
        ver = platform.mac_ver()
        _OS_VERSION = ver[0]

    elif sys.platform == 'win32':
        out = subprocess.check_output('ver', shell=True).decode().strip()
        release = out[(out.find('[Version ') + 9):-1]
        parts = [0]*4
        for i, n in enumerate(release.split('.')):
            parts[i] = int(n)
        if (parts[0] > 6 or
            (parts[0] == 6 and parts[1] > 4) or
            (parts[0] == 6 and parts[1] == 4 and parts[2] >= 9841)):
            _OS_VERSION = '10'
        elif (parts[0] == 6 and
              (parts[1] > 2 or (parts[1] ==2 and parts[2] >= 8102))):
            _OS_VERSION = '8'
        else:
            _OS_VERSION = '7'
