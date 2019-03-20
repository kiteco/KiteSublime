import os
import subprocess

__all__ = ['_launch_kite', '_locate_kite', '_is_kite_running']


def _launch_kite(app):
    return subprocess.Popen([app, '--plugin-launch'])


def _locate_kite():
    installed = False
    app = None

    if os.path.exists('/opt/kite/current'):
        installed = True
        app = os.path.join(os.path.realpath('/opt/kite/current'), 'kited')

    return installed, app


def _is_kite_running():
    out = subprocess.check_output(['ps', '-e', '-o', 'command'])
    procs = out.decode('utf-8', 'replace').strip().split('\n') if out else []
    kite_procs = [p for p in procs if p.endswith('kited')]
    return len(kite_procs) > 0
