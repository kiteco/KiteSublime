import sublime

from ..lib import link_opener

def install_kite():
    res = sublime.ok_cancel_dialog(
        'Kite Engine not installed\n\n' +
        'Kite requires the Kite Engine backend to provide completions and ' +
        'documentation. Please install it to use Kite.',
        ok_title='Install Kite'
    )
    if res:
        link_opener.open_browser_url(
            'https://github.com/kiteco/KiteSublime#installing-the-kite-engine')
