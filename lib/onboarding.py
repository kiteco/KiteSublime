import requests
import sublime

from ..lib import link_opener

def start_onboarding():
    url = 'http://localhost:46624/clientapi/plugins/onboarding_file'
    resp = requests.get(url)

    if resp.status_code != 200:
        res = sublime.yes_no_cancel_dialog(
            'Sublime Text is now integrated with Kite.\n\n' +
            'Kite is an AI-powered programming assistant that shows you ' +
            'the right information at the right time to keep you in the ' +
            'flow.\n\n' +
            'Would you like to learn how to use Kite?\n',
            yes_title='Show me what Kite can do',
            no_title='Hide forever'
        )
        if res == sublime.DIALOG_YES:
            link_opener.open_browser_url(
                'https://github.com/kiteco/KiteSublime/blob/master/README.md')
        return res == sublime.DIALOG_NO

    file_name = resp.json()
    sublime.active_window().open_file(file_name)
    return True
