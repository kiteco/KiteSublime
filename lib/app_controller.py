import subprocess

_KITE_INSTALLED = None
_KITE_APP = None


def is_kite_installed():
    if _KITE_INSTALLED is None:
        raise RuntimeError('Kite has not been located')

    return _KITE_INSTALLED


def launch_kite():
    if not is_kite_installed():
        raise RuntimeError('Kite is not installed')

    proc = subprocess.Popen(['open', _KITE_APP])
    proc.communicate()


def locate_kite():
    global _KITE_INSTALLED, _KITE_APP
    try:
        out = subprocess.check_output(
            ['mdfind', 'kMDItemCFBundleIdentifier="com.kite.Kite"'])
        _KITE_INSTALLED = len(out) > 0
        _KITE_APP = out.decode().strip() if _KITE_INSTALLED else None
    except subprocess.CalledProcessError:
        _KITE_INSTALLED = False
        _KITE_APP = None
