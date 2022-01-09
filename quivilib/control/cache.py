

from quivilib import meta
from quivilib.model.canvas import Canvas
from quivilib.util import synchronized_method

from wx.lib.pubsub import pub as Publisher
import wx

from threading import Thread, Lock, Semaphore
from queue import Queue
import logging
import traceback

log = logging.getLogger('cache')
log.setLevel(logging.ERROR)



class ImageCacheLoadRequest(object):
    def __init__(self, container, item, view):
        self.container = container
        self.item = item
        self.view = view
        self.path = item.path
        self.img = None
        
    def __call__(self, settings):
        self.canvas = Canvas('tempcanvas', settings, True)
        self.canvas.view = self.view
        item_index = self.container.items.index(self.item)
        f = self.container.open_image(item_index)
        #can't use "with" because not every file-like object used here supports it
        try:
            self.canvas.load(f, self.path, delay=True)
        finally:
            f.close()
        self.img = self.canvas.img
        
    def __eq__(self, other):
        if not other:
            return False
        cont_eq = (self.container is other.container)
        item_eq = (self.item == other.item)
        return cont_eq and item_eq
        
    def __ne__(self, other):
        return not self == other 



class ImageCache(object):
    def __init__(self, settings):
        self.settings = settings
        Publisher.subscribe(self.on_load_image, 'cache.load_image')
        Publisher.subscribe(self.on_clear_pending, 'cache.clear_pending')
        Publisher.subscribe(self.on_flush, 'cache.flush')
        Publisher.subscribe(self.on_program_closed, 'program.closed')
        self.queue = []
        self.qlock = Lock()
        self.cache = []
        self.clock = Lock()
        self.semaphore = Semaphore(0)
        self.thread = Thread(target=self.run)
        self.thread.setDaemon(True)
        self.thread.start()
        self.processing_request = None
        
    def on_load_image(self, message):
        request = message.data
        hit = False 
        with self.clock:
            for req in self.cache:
                if req == request:
                    log.debug('main: cache hit')
                    self.notify_image_loaded(req)
                    hit = True
        if not hit and request != self.processing_request:
            log.debug('main: cache miss')
            self._put_request(request)
            
    def on_image_loaded(self, request):
        with self.clock:
            if len(self.cache) >= meta.CACHE_SIZE:
                self.cache.pop()
            self.cache.insert(0, request)
            request.img.delayed_load()
            self.notify_image_loaded(request)
            
    def on_flush(self, message):
        with self.clock:
            while self.cache:
                self.cache.pop()
                
    def notify_image_loaded(self, request):
        Publisher.sendMessage('cache.image_loaded', request)
        
    def notify_image_load_error(self, request, exception, tb):
        Publisher.sendMessage('cache.image_load_error', (request, exception, tb))
        
    def _put_request(self, request):
        with self.qlock:  
            if request not in self.queue:
                log.debug('main: inserting request')
                self.queue.insert(0, request)
                log.debug('main: releasing...')
                self.semaphore.release()
            
    def on_clear_pending(self, message):
        with self.qlock:
            while self.queue:
                self.queue.pop()
                
    def on_program_closed(self, message):
        log.debug('main: on closed')
        #log.debug('main: clearing pending...')
        self.on_clear_pending(None)
        with self.qlock:
            log.debug('main: adding None request')
            self.queue.insert(-1, None)
        log.debug('main: releasing...')
        self.semaphore.release()
        log.debug('main: joining...')
        self.thread.join()
    
    def run(self):
        log.debug('thread: running...')
        while True:
            log.debug('thread: acquiring...')
            self.semaphore.acquire()
            log.debug('thread: acquired. reading request...')
            while True:
                with self.qlock:
                    if not self.queue:
                        log.debug('thread: queue empty')
                        break
                    req = self.queue.pop()
                if req is None:
                    return
                self.processing_request = req
                e, tb = None, None
                try:
                    log.debug('thread: running request...')
                    req(self.settings)
                    log.debug('thread: request processed, notifying')
                    wx.CallAfter(self.on_image_loaded, req)
                    log.debug('thread: request processed notified')
                except Exception as ex:
                    tb = traceback.format_exc()
                    log.debug('thread: request raised an exception')
                    e = ex
                    #log.debug(tb)
                finally:
                    self.processing_request = None
                if tb:
                    wx.CallAfter(self.notify_image_load_error, req, e, tb)
                
