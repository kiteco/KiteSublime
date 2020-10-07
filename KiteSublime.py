from .setup import *; setup_all()
from .lib.languages import Languages

import sublime

if int(sublime.version()[0]) < 3:
    sublime.error_message(
        'Package KiteSublime does not work on your version of Sublime.\n\n' +
        'Sublime will disable this package.'
    )
    raise ImportError('unsupported Sublime: {}'.format(sublime.version()))

import sys

if sys.platform not in ('darwin', 'win32', 'linux', 'linux2'):
    sublime.error_message(
        'Package KiteSublime is not supported on your OS.\n\n' +
        'Sublime will disable this package.'
    )
    raise ImportError('unsupported platform: {}'.format(sys.platform))

from .lib import app_controller, deferred, logger, reporter
from .lib import installer, onboarding, settings
from .lib.commands import *
from .lib.handlers import *

_consumer = None


def plugin_loaded():
    """Called when the plugin is first loaded. Sets up an exception handler
    to forward uncaught exceptions to Rollbar, instantiates a single consumer
    instance to handle deferred events, and locates and starts the Kite
    Engine if available.
    """
    app_controller.locate_kite()
    kite_installed = app_controller.is_kite_installed()

    if not kite_installed:
        installer.install_kite()
    elif reporter.check_reporting_enabled():
        reporter.setup_excepthook()

    global _consumer
    _consumer = deferred.consume()

    setup_completion_rules()

    if kite_installed:
        if settings.get('start_kite_engine_on_startup', True):
            app_controller.launch_kite_if_not_running()

        if settings.get('show_help_dialog', True):
            onboarding.open_tutorial(Languages.PYTHON)

    logger.log('Kite v{} activated'.format(package_version()))


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
