import requests
import sublime

from ..lib import link_opener, settings, app_controller
from ..lib.link_opener import open_copilot_root
from ..lib.languages import Languages, Extensions, LEXICAL_EXTS, SUPPORTED_EXTS_TO_LANG, ext_to_lang, kited_ext_enabled


def start_onboarding(ext):
    """Attempts to open the live onboarding file for a given language.
    If fetching the file fails, then a help dialog is shown instead.
    """
    lang = ext_to_lang(ext).lower()
    url = 'http://localhost:46624/clientapi/plugins/onboarding_file'
    resp = requests.get(url, params={'editor': 'sublime3', 'language': lang})

    if resp.status_code != 200:
        show_help_notif(ext)
    else:
        file_name = resp.json()
        sublime.active_window().open_file(file_name)
    mark_help_shown(ext)


def show_help_notif(ext):
    """ Shows a language specific dialogue that links to a help page
    for that language.
    """
    if ext == Extensions.PY:
        res = sublime.yes_no_cancel_dialog(
            'Sublime Text is now integrated with Kite for Python.\n\n' +
            'Kite provides ML-powered completions and instant ' +
            'documentation for Python to help keep you in the flow.\n\n' +
            'Would you like to learn how to use Kite for Python?\n',
            yes_title='Show me what Kite can do',
            no_title='Hide forever'
        )
        if res == sublime.DIALOG_YES:
            link_opener.open_browser_url(
                'https://github.com/kiteco/KiteSublime/blob/master/README.md')

    # Beta will be changed to help page for each lexical language
    elif ext in LEXICAL_EXTS:
        lang = ext_to_lang(ext)
        res = sublime.yes_no_cancel_dialog(
            'Welcome to Kite for '+lang+' Beta!\n\n' +
            'You\'ve got access to our line-of-code completions for '+lang+', ' +
            'powered by machine learning. If you\'d like to disable beta, ' +
            'you can do so in the Copilot',
            yes_title='Hide Forever',
            no_title='Open Copilot'
        )
        if res == sublime.DIALOG_NO:
            app_controller.launch_kite_if_not_running()
            open_copilot_root('')


def mark_help_shown(ext):
    """ Handles logic for flagging languages for subsequent onboarding shown.
    """
    if ext == Extensions.PY:
        # If a user has seen Python onboarding, they shouldn't see any other onboarding
        onboarded = SUPPORTED_EXTS_TO_LANG.values()
    elif ext in LEXICAL_EXTS:
        # Once a user has been through lexical onboarding, they shouldn't see other
        # lexical onboarding (but they can see Python onboarding).
        onboarded = map(ext_to_lang, LEXICAL_EXTS)
    else:
        raise Exception("Unexpected: marking help shown for non-lexical/Python file.")

    for lang in onboarded:
        settings.set('show_'+lang.lower()+'_help', False)


def should_onboard(ext):
    """ Determines if onboarding for a particular language should be shown.
    """
    if ext not in SUPPORTED_EXTS_TO_LANG:
        return False

    # For legacy behavior. Should fallback to new behavior if not present.
    if ext == Extensions.PY and not settings.get('show_help_dialog', True):
        return False

    lang = ext_to_lang(ext)
    return settings.get('show_'+lang.lower()+'_help', True) and kited_ext_enabled(ext)
