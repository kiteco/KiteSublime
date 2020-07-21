import sublime

import json
import os
import platform
import subprocess
import sys
from shutil import copyfile
from re import findall

_ROOT = None
_DEVELOPMENT = False
_OS_VERSION = ''
_PACKAGE_VERSION = None


def setup_all():
    global _DEVELOPMENT
    global _PACKAGE_VERSION
    _setup_path()
    _setup_os_version()
    if os.path.exists(os.path.join(_ROOT, 'DEVELOPMENT')):
        os.environ['SUBLIME_DEV'] = '1'
        _DEVELOPMENT = True
    with open(os.path.join(_ROOT, 'package.json')) as f:
        pkg = json.loads(f.read())
        _PACKAGE_VERSION = pkg.get('version', None)


def setup_completion_rules():
    src = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'assets',
                       'Completion Rules.tmPreferences')
    dest = os.path.join(sublime.packages_path(), 'Python',
                        'Completion Rules.tmPreferences')
    if not os.path.exists(dest):
        if not os.path.exists(os.path.dirname(dest)):
            os.makedirs(os.path.dirname(dest))
        copyfile(src, dest)


def is_development():
    return _DEVELOPMENT


def is_same_package(filename):
    return filename.startswith(_ROOT)


def os_version():
    return _OS_VERSION


def package_version():
    return _PACKAGE_VERSION


def _setup_path():
    global _ROOT
    _ROOT = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))
    sys.path.append(os.path.join(_ROOT, 'vendor'))


def _setup_os_version():
    global _OS_VERSION

    if sys.platform == 'darwin':
        ver = platform.mac_ver()
        _OS_VERSION = ver[0]

    elif sys.platform == 'win32':
        out = str(subprocess.check_output('ver', shell=True).strip())
        pattern = r'(?<=\s)\d+.*(?=\])'
        release = findall(pattern, out)[0]
        parts = [0] * 4
        for i, n in enumerate(release.split('.')):
            parts[i] = int(n)
        if (parts[0] > 6 or
                (parts[0] == 6 and parts[1] > 4) or
                (parts[0] == 6 and parts[1] == 4 and parts[2] >= 9841)):
            _OS_VERSION = '10'
        elif (parts[0] == 6 and
                (parts[1] > 2 or (parts[1] == 2 and parts[2] >= 8102))):
            _OS_VERSION = '8'
        else:
            _OS_VERSION = '7'
