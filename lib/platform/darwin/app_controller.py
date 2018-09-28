import subprocess

__all__ = ['_launch_kite', '_locate_kite']

def _launch_kite(app):
    proc = subprocess.Popen(['open', app])
    return proc

def _locate_kite():
    installed = None
    app = None

    try:
        out = subprocess.check_output(
            ['mdfind', 'kMDItemCFBundleIdentifier="com.kite.Kite"'])
        installed = len(out) > 0
        app = (out.decode().strip().split('\n')[0] if installed
               else None)
    except subprocess.CalledProcessError:
        installed = False
        app = None
    finally:
        return (installed, app)
