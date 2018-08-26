import subprocess

def open_browser(ident):
    proc = subprocess.Popen(['open',
                             'https://kite.com/python/docs/{}'.format(ident)])
    return proc.communicate()

def open_copilot(ident):
    proc = subprocess.Popen(['open',
                             'kite://docs/{}'.format(ident)])
    return proc.communicate()
