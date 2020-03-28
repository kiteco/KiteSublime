import requests
import sublime

from ..lib import link_opener, languages, settings

def start_onboarding(ext):
    """Attempts to open the live onboarding file for a given language. 
    If fetching the file fails, then a help dialog is shown instead.
    """
    lang = languages.ext_to_lang(ext).lower()
    url = 'http://localhost:46624/clientapi/plugins/onboarding_file'
    resp = requests.get(url, params={'editor': 'sublime3', "language": lang})

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
        settings.set("should_onboard_"+lang, False)
        return

    file_name = resp.json()
    sublime.active_window().open_file(file_name)
    settings.set("should_onboard_"+lang, False)

def should_onboard_lang(ext):
    if ext not in languages.SUPPORTED_EXTS_TO_LANG:
        return False

    # For legacy behavior. Should fallback to new behavior if not present.
    if ext == ".py" and not settings.get("show_help_dialog", True):
        return False

    lang = languages.ext_to_lang(ext).lower()
    return settings.get("should_onboard_"+lang, True) and languages.kited_ext_enabled(ext)