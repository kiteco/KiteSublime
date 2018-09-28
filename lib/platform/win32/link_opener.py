import subprocess

__all__ = ['_open_browser', '_open_copilot']

def _open_browser(ident):
    proc = subprocess.Popen(['explorer',
                             'https://kite.com/python/docs/{}'.format(ident)])
    return proc.communicate()

def _open_copilot(ident):
    proc = subprocess.Popen(['explorer',
                             'kite://docs/{}'.format(ident)])
    return proc.communicate()
