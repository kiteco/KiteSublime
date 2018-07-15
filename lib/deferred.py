import time
from queue import Empty, Full, Queue
from threading import Lock, Thread

from ..lib import logger


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
    def __init__(self, queue, handler):
        self.queue = queue
        self.handler = handler
        self.thread = None
        self.lock = Lock()
        self.consuming = False

    def start(self):
        with self.lock:
            if self.consuming:
                return
            self.consuming = True
            self.thread = Thread(target=self._consume)
            self.thread.start()

    def stop(self):
        with self.lock:
            self.consuming = False
            self.thread.join()

    def _consume(self):
        while self.consuming:
            try:
                payload = self.queue.get(block=False)
                self.handler(payload)
            except Empty:
                pass
            time.sleep(0.1)


def defer(func, *args, **kwargs):
    try:
        done = kwargs.pop('_done', None)
        payload = {
            'func': func,
            'args': args,
            'kwargs': kwargs,
            'done': done,
        }
        _queue.put(payload, block=False)
    except Full:
        logger.log("skipping defer because queue is full")

def consume():
    c = Consumer(_queue, _handler)
    c.start()
    return c
