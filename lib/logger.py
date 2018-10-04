import datetime
import json

def log(msg):
    print('[Kite] {} | {}'.format(_ts(), msg))

def jsonstr(obj):
    return json.dumps(obj, indent=2)

def _ts():
    return datetime.datetime.now().strftime('%m/%d/%y %H:%M:%S.%f')[:-3]
