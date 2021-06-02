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
            sublime.message_dialog(
            'Kite requires the Kite Engine backend to provide completions and\n' +
            'documentation. However, the Kite Engine is currently unavailable\n' +
            'for download. When the Kite Engine is available again, you will be\n' +
            'notified on Sublime startup.'
            )
            settings.set('has_seen_download_unavailable_dialog', True)
