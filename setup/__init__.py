import os
import sublime
import sys

from ..lib import logger

_ROOT = None

def setup_all():
    _setup_path()
    if os.path.exists(os.path.join(_ROOT, 'DEVELOPMENT')):
        os.environ['SUBLIME_DEV'] = '1'

def _setup_path():
    global _ROOT
    _ROOT = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))
    sys.path.append(os.path.join(_ROOT, 'vendor'))
