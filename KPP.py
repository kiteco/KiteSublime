from .setup import setup_all; setup_all()

import sublime

from .lib import deferred, logger
from .lib.commands import *
from .lib.handlers import *

_consumer = None

def plugin_loaded():
    """Called when the plugin is first loaded. Instantiates a single consumer
    instance to handle deferred events.
    """
    global _consumer
    _consumer = deferred.consume()
    logger.log('KPP activated')

def plugin_unloaded():
    """Called before the plugin is unloaded. Stops the consumer immediately
    without waiting for the queue to be empty.
    """
    if _consumer:
        _consumer.stop()
    logger.log('KPP deactivated')
