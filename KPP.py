import sublime

from .lib import deferred
from .lib.listeners import *

_consumer = None

def plugin_loaded():
    """ Called when the plugin is first loaded
    """
    global _consumer
    _consumer = deferred.consume()
    print("KPP activated")

def plugin_unloaded():
    """ Called before the plugin is unloaded
    """
    if _consumer:
        _consumer.stop()
    print("KPP deactivated")
