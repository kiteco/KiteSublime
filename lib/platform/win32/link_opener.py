import subprocess

__all__ = [
    '_open_browser', '_open_browser_url',
    '_open_copilot', '_open_copilot_root',
]

def _open_browser(ident):
    proc = subprocess.Popen(['explorer',
                             'https://kite.com/python/docs/{}'.format(ident)])
    return proc.communicate()

def _open_browser_url(url):
    proc = subprocess.Popen(['explorer', url])
    return proc.communicate()

def _open_copilot(ident):
    proc = subprocess.Popen(['explorer',
                             'kite://docs/{}'.format(ident)])
    return proc.communicate()

def _open_copilot_root(path):
    proc = subprocess.Popen(['explorer',
                             'kite://{}'.format(path)])
    return proc.communicate()
