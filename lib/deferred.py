import sys
import time
import traceback
from queue import Empty, Full, Queue
from threading import Lock, Thread

from ..lib import logger, reporter
from ..lib.errors import ExpectedError
from ..setup import is_same_package

# A global queue that is used for the convenience methods provided below.
_queue = Queue(maxsize=8)


def _handler(payload):
    func = payload.get('func')
    args = payload.get('args', [])
    kwargs = payload.get('kwargs', {})
    done = payload.get('done')
    if func:
        res = func(*args, **kwargs)
        if done:
            done(res)


def _pop(queue):
    try:
        queue.get(block=False)
    except Empty:
        pass


class Consumer:
    """Consumer class which consumes events from a queue. Consumption occurs
    in a separate thread. Multiple consumers can consume from the same queue
    since synchronization is done implicitly by the queue data type.
    """

    def __init__(self, queue, handler):
        """Initialize a consumer. This constructor does not start consumption.
        Instead, the caller of this method should also call `start` to start
        consumption.

        Arguments:
            queue: An instance of a `Queue` class to consume events from.
            handler: A function which is called on the events taken from the
                queue.
        """
        self.queue = queue
        self.handler = handler
        self.thread = None
        self.lock = Lock()
        self.consuming = False

    def start(self):
        """Start consuming from the queue in a separate thread.
        """
        with self.lock:
            if self.consuming:
                return
            self.consuming = True
            self.thread = Thread(target=self._consume)
            self.thread.start()

    def stop(self):
        """Stop consuming and join the underlying thread.
        """
        with self.lock:
            self.consuming = False
            self.thread.join()

    def _consume(self):
        """The consumption loop in which events are pulled from the queue
        and handled by the consumer. All exceptions are caught in order to
        prevent the underlying thread from stopping unncessarily.
        """
        while self.consuming:
            try:
                payload = self.queue.get(block=False)
                self.handler(payload)
            except Empty:
                time.sleep(0.01)
            except ExpectedError as exc:
                logger.debug('caught expected {}: {}'
                             .format(exc.__class__.__name__, str(exc)))
            except Exception as exc:
                reporter.send_rollbar_exc(sys.exc_info())
                logger.debug('caught {}: {}'
                             .format(exc.__class__.__name__, str(exc)))


def defer(func, *args, **kwargs):
    """Defer a function call to be executed asynchronously in the background.
    If the queue is full, then this function call will either be ignored or
    forced onto the queue depending on the presence and value of an optional
    `_force` argument.

    A `_force` argument can be passed into the keyword arguments to control
    whether or not the function call should be forced onto the queue. If this
    argument is true and the queue is full when this function is called, then
    the oldest item on the queue will be dropped and the defer call will be
    retried. The `_force` argument defaults to true.

    A `_done` callback can be passed into the keyword arguments. If this
    callback is present, it will be called on the return value of the executed
    function.

    Arguments:
        func: The function to execute.
        args: The positional arguments to pass to the function.
        kwargs: The keyword arguments to pass to the function.

    Returns:
        True if the function call was queued successfully, False otherwise.
    """
    done = kwargs.pop('_done', None)
    force = kwargs.pop('_force', True)

    try:
        payload = {
            'func': func,
            'args': args,
            'kwargs': kwargs,
            'done': done,
        }
        _queue.put(payload, block=False)
        return True
    except Full:
        if not force:
            logger.debug('skipping defer because queue is full')
            return False
        else:
            logger.debug('forcing defer because queue is full')
            _pop(_queue)
            kwargs.update({'_done': done, '_force': force})
            return defer(func, *args, **kwargs)


def consume():
    """Create a consumer and start the consumption loop. This function needs
    to be called at least once in order for the `defer` function to have any
    meaningful effect.
    """
    c = Consumer(_queue, _handler)
    c.start()
    return c
