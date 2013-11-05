import Queue
import threading

class ThreadPool(object):
    def __init__(self):
        self.queue = Queue.Queue()

    def enqueue(self, func, *args, **kwargs):
        self.queue.put((func, args, kwargs))

    def work(self, concurrency):
        threads = []
        for _ in xrange(concurrency):
            t = threading.Thread(target=self.thread)
            t.start()
            threads.append(t)
        for t in threads:
            t.join()

    def thread(self):
        while not self.queue.empty():
            func, args, kwargs = self.queue.get_nowait()
            func(*args, **kwargs)

class Flag(object):
    def __init__(self, value=False):
        self.value = value
        self.lock = threading.RLock()

    def set_value(self, value):
        with self.lock:
            self.value = value

