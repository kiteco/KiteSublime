import subprocess

from ....lib import logger

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
            logger.log('found Kite installation:\n{}'.format(out.decode()))
            res = out.decode().strip().split('\n')[1].strip()
            app = '{}\\kited.exe'.format(res[res.find('C:\\'):])
    except subprocess.CalledProcessError:
        installed = False
        app = None
    finally:
        logger.log('located kite: ({}, {})'.format(installed, app))
        return (installed, app)
