import os
import subprocess
import sys

from ....lib import reporter

__all__ = ['_launch_kite', '_locate_kite', '_is_kite_running']

_QUERY = 'reg query "HKEY_LOCAL_MACHINE\\Software\\Kite\\AppData" /v ' \
         'InstallPath /s /reg:64 '


def _launch_kite(app):
    env = os.environ.copy()
    env['KITE_SKIP_ONBOARDING'] = '1'
    proc = subprocess.Popen([app], env=env)
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


def _is_kite_running():
    running = False

    try:
        out = subprocess.check_output('tasklist /FI "IMAGENAME eq kited.exe')
        if len(out) > 0:
            res = out.decode('utf-8', 'replace')
            running = 'kited.exe' in res
    except (subprocess.CalledProcessError, UnicodeDecodeError) as ex:
        reporter.send_rollbar_exc(sys.exc_info())
        return running
    finally:
        return running
