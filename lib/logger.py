import datetime
import json

from ..lib import settings
from ..setup import is_development

def log(msg):
    print('[Kite] {} | {}'.format(_ts(), msg))

def debug(msg, if_development=True, if_verbose=True):
    if ((if_development and is_development()) or
        (if_verbose and settings.get('verbose_logs', False))):
        log(msg)

def jsonstr(obj):
    return json.dumps(obj, indent=2)

def _ts():
    return datetime.datetime.now().strftime('%m/%d/%y %H:%M:%S.%f')[:-3]
