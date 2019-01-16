import subprocess
import sys

from ....lib import reporter

__all__ = ['_launch_kite', '_locate_kite', '_is_kite_running']


def _launch_kite(app):
    subprocess.check_output(['defaults', 'write', 'com.kite.Kite',
                             'shouldReopenSidebar', '0'])
    proc = subprocess.Popen(['open', '-a', app, '--args', '"--plugin-launch"'])
    return proc


def _locate_kite():
    installed = False
    app = None

    try:
        out = subprocess.check_output(
            ['mdfind', 'kMDItemCFBundleIdentifier="com.kite.Kite"'])
        installed = len(out) > 0
        app = (out.decode('utf-8', 'replace').strip().split('\n')[0]
               if installed else None)
    except (subprocess.CalledProcessError, UnicodeDecodeError) as ex:
        reporter.send_rollbar_exc(sys.exc_info())
        installed = False
        app = None
    finally:
        return (installed, app)


def _is_kite_running():
    out = subprocess.check_output(['ps', '-axco', 'command'])
    procs = out.decode('utf-8', 'replace').strip().split('\n') if out else []
    return 'Kite' in procs
