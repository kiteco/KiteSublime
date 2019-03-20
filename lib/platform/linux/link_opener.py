import subprocess

__all__ = [
    '_open_browser', '_open_browser_url',
    '_open_copilot', '_open_copilot_root'
]

def _open_browser(ident):
    proc = subprocess.Popen(['xdg-open',
                             'https://kite.com/python/docs/{}'.format(ident)])
    return proc.communicate()

def _open_browser_url(url):
    proc = subprocess.Popen(['xdg-open', url])
    return proc.communicate()

def _open_copilot(ident):
    proc = subprocess.Popen(['xdg-open',
                             'kite://docs/{}'.format(ident)])
    return proc.communicate()

def _open_copilot_root(path):
    proc = subprocess.Popen(['xdg-open',
                             'kite://{}'.format(path)])
    return proc.communicate()
