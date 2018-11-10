import sublime

from ..lib import link_opener

def check_anaconda_compatibility():
    cfg = sublime.load_settings('Anaconda.sublime-settings')
    if (cfg.get('disable_anaconda_completion') == False or
        cfg.get('display_signatures')):
        ok = sublime.ok_cancel_dialog(
            '[Kite] Kite may not work properly with your current ' +
            'configuration of Anaconda.\n\n' +
            'You can disable Anaconda\'s completions and signatures ' +
            'temporarily to fix this issue.\n',
            ok_title='Show me how'
        )
        if ok:
            link_opener.open_browser_url(
                'https://help.kite.com/article/81-kite-and-anaconda')
