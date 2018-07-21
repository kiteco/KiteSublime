import os
import sublime
import sys

from ..lib import logger

def setup_all():
    _setup_path()

def _setup_path():
    root_path = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))
    sys.path.append(os.path.join(root_path, 'vendor'))
