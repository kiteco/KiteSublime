import datetime

def log(msg):
    print('[KPP] {} | {}'.format(_ts(), msg))

def _ts():
    return datetime.datetime.now().strftime('%m/%d/%y %H:%M:%S')
