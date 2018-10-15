import subprocess

__all__ = ['_launch_kite', '_locate_kite']

_QUERY = 'reg query "HKEY_LOCAL_MACHINE\\Software\\Kite\\AppData" /v InstallPath /s /reg:64'

def _launch_kite(app):
    proc = subprocess.Popen([app])
    return proc

def _locate_kite():
    installed = None
    app = None

    try:
        out = subprocess.check_output(_QUERY)
        installed = len(out) > 0
        if installed:
            res = out.decode().strip().split('\n')[1].strip()
            app = '{}\\kited.exe'.format(res[res.find('C:\\'):])
    except subprocess.CalledProcessError:
        installed = False
        app = None
    finally:
        return (installed, app)
