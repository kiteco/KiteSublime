import sublime

from ..lib import app_controller, link_opener, settings

def install_kite():
    download_available = app_controller.can_download_kite()
    if download_available:
        res = sublime.ok_cancel_dialog(
            'Kite is missing dependencies\n\n' +
            'Kite requires the Kite Engine backend to provide completions and ' +
            'documentation. Please install it to use Kite.\n',
            ok_title='Install Kite'
        )
        if res:
            link_opener.open_browser_url(
                'https://kite.com/download/?utm_source=sublime-plugin')
    else:
        already_seen_dialog = settings.get('has_seen_download_unavailable_dialog', False)
        if not already_seen_dialog:
            more_info = sublime.ok_cancel_dialog(
            'Kite requires the Kite Engine application to function. Unfortunately\n' +
            'the Kite Engine is unavailable to download for the next few weeks.\n' +
            'This plugin will let you know when it is available.\n\n' +
            "For more information, click the 'More Info' button below.",
            ok_title='More Info'
            )
            settings.set('has_seen_download_unavailable_dialog', True)
            if more_info:
                link_opener.open_browser_url(
                    'https://kite.com/kite-is-temporarily-unavailable/?source=sublime-plugin')
