import os
import requests
import subprocess

import sublime

__all__ = ['_launch_kite', '_locate_kite', '_is_kite_running', '_can_download_kite']


def _launch_kite(app):
    return subprocess.Popen([app, '--plugin-launch'])


def _locate_kite():
    installed = False
    app = None

    if os.path.exists(os.path.expanduser('~/.local/share/kite/kited')):
        installed = True
        app = os.path.realpath(os.path.expanduser('~/.local/share/kite/kited'))

    elif os.path.exists('/opt/kite/kited'):
        installed = True
        app = os.path.realpath('/opt/kite/kited')

    return installed, app


def _is_kite_running():
    out = subprocess.check_output(['ps', '-e', '-o', 'command'])
    procs = out.decode('utf-8', 'replace').strip().split('\n') if out else []
    kite_procs = [p for p in procs if p.endswith('kited')]
    return len(kite_procs) > 0


def _can_download_kite():
    try:
        r = requests.head("https://linux.kite.com/dls/linux/current", allow_redirects=True, timeout=10)
        return r.ok
    except requests.ConnectionError:
        return False
    return False
