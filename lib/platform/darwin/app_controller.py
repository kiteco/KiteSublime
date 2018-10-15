import subprocess

__all__ = ['_launch_kite', '_locate_kite']

def _launch_kite(app):
    subprocess.check_output(['defaults', 'write', 'com.kite.Kite',
                             'shouldReopenSidebar', '0'])
    proc = subprocess.Popen(['open', '-a', app, '--args', '"--plugin-launch"'])
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
