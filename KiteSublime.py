from .setup import setup_all; setup_all()

import sublime

import sys
if sys.platform not in ('darwin', 'win32'):
    sublime.error_message(
        'Package KiteSublime is not supported on your OS.\n\n' +
        'Sublime will disable this package.'
    )
    raise ImportError('unsupported platform: {}'.format(sys.platform))

from .lib import app_controller, deferred, logger, reporter
from .lib import settings, link_opener
from .lib.commands import *
from .lib.handlers import *

_consumer = None


def plugin_loaded():
    """Called when the plugin is first loaded. Sets up an exception handler
    to forward uncaught exceptions to Rollbar, instantiates a single consumer
    instance to handle deferred events, and locates and starts the Kite
    Engine if available.
    """
    reporter.setup_excepthook()

    global _consumer
    _consumer = deferred.consume()

    app_controller.locate_kite()
    if app_controller.is_kite_installed():
        app_controller.launch_kite()

    if settings.get('show_help_dialog', True):
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
        elif res == sublime.DIALOG_NO:
            settings.set('show_help_dialog', False)

    logger.log('Kite activated')


def plugin_unloaded():
    """Called before the plugin is unloaded. Stops the consumer immediately
    without waiting for the queue to be empty and removes the uncaught
    exception handler. Also removes the Kite status from all the currently
    open views.
    """
    if _consumer:
        _consumer.stop()

    reporter.release_excepthook()

    StatusHandler.erase_all_statuses()

    logger.log('Kite deactivated')
