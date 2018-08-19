import time
from queue import Empty, Full, Queue
from threading import Lock, Thread

from ..lib import logger

# A global queue that is used for the convenience methods provided below.
_queue = Queue(maxsize=32)

def _handler(payload):
    func = payload.get('func')
    args = payload.get('args', [])
    kwargs = payload.get('kwargs', {})
    done = payload.get('done')
    if func:
        res = func(*args, **kwargs)
        if done:
            done(res)


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
            except Exception as ex:
                logger.log('caught {}: {}'
                           .format(ex.__class__.__name__, str(ex)))


def defer(func, *args, **kwargs):
    """Defer a function call to be executed asynchronously in the background.
    If the queue is full, then this function call will be ignored.

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
    try:
        done = kwargs.pop('_done', None)
        payload = {
            'func': func,
            'args': args,
            'kwargs': kwargs,
            'done': done,
        }
        _queue.put(payload, block=False)
        return True
    except Full:
        logger.log('skipping defer because queue is full')
        return False

def consume():
    """Create a consumer and start the consumption loop. This function needs
    to be called at least once in order for the `defer` function to have any
    meaningful effect.
    """
    c = Consumer(_queue, _handler)
    c.start()
    return c
