import requests
import sublime

from ..lib import link_opener, settings


def open_tutorial(lang):
    """Attempts to open the language specific tutorial file.
    If fetching the file fails, then a help dialog is shown instead.
    """
    lang = lang.lower()
    url = 'http://localhost:46624/clientapi/plugins/onboarding_file'
    try:
        resp = requests.get(url, params={'editor': 'sublime3', 'language': lang})
        if resp.status_code == 200:
            file_name = resp.json()
            sublime.active_window().open_file(file_name)
        else:
            show_help_dialog()
    except:
        show_help_dialog()

    settings.set('show_help_dialog', False)

def show_help_dialog():
    """ Shows a dialogue that links to a help page
    """
    res = sublime.yes_no_cancel_dialog(
        'Sublime Text is now integrated with Kite.\n\n' +
        'Kite provides ML-powered completions to help keep you in the flow.\n\n' +
        'Would you like to learn how to use Kite?\n',
        yes_title='Show me what Kite can do',
        no_title='Hide forever'
    )

    if res == sublime.DIALOG_YES:
        link_opener.open_browser_url(
            'https://github.com/kiteco/KiteSublime/blob/master/README.md')
