import subprocess
import sys

from ....lib import reporter

__all__ = ['_launch_kite', '_locate_kite']

_QUERY = 'reg query "HKEY_LOCAL_MACHINE\\Software\\Kite\\AppData" /v InstallPath /s /reg:64'

def _launch_kite(app):
    proc = subprocess.Popen([app])
    return proc

def _locate_kite():
    installed = False
    app = None

    try:
        out = subprocess.check_output(_QUERY)
        if len(out) > 0:
            res = out.decode('utf-8', 'replace').strip().split('\n')[1].strip()
            app = '{}\\kited.exe'.format(res[res.find('C:\\'):])
            installed = True
    except (subprocess.CalledProcessError, UnicodeDecodeError) as ex:
        reporter.send_rollbar_exc(sys.exc_info())
        installed = False
        app = None
    finally:
        return (installed, app)
