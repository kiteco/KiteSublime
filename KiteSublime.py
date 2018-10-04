from .setup import setup_all; setup_all()

import sublime

from .lib import app_controller, deferred, logger, reporter
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

    logger.log('Kite activated')


def plugin_unloaded():
    """Called before the plugin is unloaded. Stops the consumer immediately
    without waiting for the queue to be empty and removes the uncaught
    exception handler.
    """
    if _consumer:
        _consumer.stop()

    reporter.release_excepthook()

    logger.log('Kite deactivated')
