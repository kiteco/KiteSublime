import sublime

from .lib import deferred, logger
from .lib.listeners import *

_consumer = None

def plugin_loaded():
    """Called when the plugin is first loaded
    """
    global _consumer
    _consumer = deferred.consume()
    logger.log("KPP activated")

def plugin_unloaded():
    """Called before the plugin is unloaded
    """
    if _consumer:
        _consumer.stop()
    logger.log("KPP deactivated")
