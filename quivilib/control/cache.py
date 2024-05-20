import logging
import traceback
from threading import Thread, Lock, Semaphore
from queue import Queue
from pubsub import pub as Publisher
import wx
from quivilib import meta
from quivilib.model.canvas import Canvas
from quivilib.util import synchronized_method

log = logging.getLogger('cache')
log.setLevel(logging.ERROR)

#TODO: The image cache is a simple queue. Items are never re-ordered.
#If an image is requested that is already loaded, it should move that image to the top
#Right now it is possible for the cache to dump the currently-displayed image due to pre-loading the next page,
#which is kinda silly.

#TODO: I want to save the resolution for any image that has been loaded, even if it is unloaded.
#Should that go in here?


class ImageCacheLoadRequest(object):
    def __init__(self, container, item, view):
        self.container = container
        self.item = item
        self.view = view
        self.path = item.path
        self.img = None
        
    def __call__(self, settings):
        canvas = Canvas('tempcanvas', settings, True)
        canvas.view = self.view
        item_index = self.container.items.index(self.item)
        f = self.container.open_image(item_index)
        assert f is not None, "Failed to open image from container"
        #can't use "with" because not every file-like object used here supports it
        try:
            canvas.load(f, self.path, delay=True)
        finally:
            f.close()
        self.img = canvas.img
        
    def __eq__(self, other):
        if not other:
            return False
        cont_eq = (self.container is other.container)
        item_eq = (self.item == other.item)
        return cont_eq and item_eq
        
    def __hash__(self):
        return hash(self.container, self.item)
        
    def __ne__(self, other):
        return not self == other 
    def __repr__(self):
        return f'<ImageCacheLoadRequest: {self.path}>'


class ImageCache(object):
    def __init__(self, settings):
        self.settings = settings
        Publisher.subscribe(self.on_load_image, 'cache.load_image')
        Publisher.subscribe(self.on_clear_pending, 'cache.clear_pending')
        Publisher.subscribe(self.on_flush, 'cache.flush')
        Publisher.subscribe(self.on_program_closed, 'program.closed')
        self.queue = []
        self.q_lock = Lock()
        self.cache = []
        self.c_lock = Lock()
        self.semaphore = Semaphore(0)
        self.thread = Thread(target=self.run, daemon=True)
        self.thread.start()
        self.processing_request = None
        
    def on_load_image(self, *, request):
        """Add a ImageCacheLoadRequest to the queue.
        Invoked by message passing.
        """
        hit = False 
        with self.c_lock:
            for req in self.cache:
                if req == request:
                    log.debug('main: cache hit')
                    self.notify_image_loaded(req)
                    hit = True
        if not hit and request != self.processing_request:
            log.debug('main: cache miss')
            self._put_request(request)
            
    def on_image_loaded(self, request):
        """ Called by the forked thread after the image is loaded. Handles the queue and message passing.
        """
        with self.c_lock:
            if len(self.cache) >= meta.CACHE_SIZE:
                removed = self.cache.pop()
                self.notify_cache_removed(removed)
            self.cache.insert(0, request)
            request.img.delayed_load()
            self.notify_image_loaded(request)
            
    def on_flush(self):
        """ Clear out the cache.
        Invoked by message passing.
        TODO: This does not clear out the queue. Shouldn't it?
        """
        with self.c_lock:
            self.cache.clear()

    def notify_image_loaded(self, request):
        """ Send message notifying of load completion.
        """
        Publisher.sendMessage('cache.image_loaded', request=request)
        
    def notify_image_load_error(self, request, exception, tb):
        """ Send message notifying of load failure.
        """
        Publisher.sendMessage('cache.image_load_error', request=request, exception=exception, tb=tb)
    
    def notify_cache_removed(self, request):
        """ Send message notifying of removal from cache (i.e. due to hitting the size limit).
        This is only used by the debug window, so do nothing in a packaged build.
        """
        if __debug__:
            Publisher.sendMessage('cache.image_removed', request=request)

    def _put_request(self, request):
        with self.q_lock:  
            if request not in self.queue:
                log.debug('main: inserting request')
                self.queue.insert(0, request)
                log.debug('main: releasing...')
                self.semaphore.release()
            
    def on_clear_pending(self, *, request=None):
        """ Clear out the processing queue. parameter is passed in but not used.
        Invoked by message passing.
        """
        with self.q_lock:
            self.queue.clear()

    def on_program_closed(self, *, settings_lst=None):
        """Cleanup thread during program close.
        Invoked by message passing.
        """
        log.debug('main: on closed')
        #log.debug('main: clearing pending...')
        self.on_clear_pending()
        with self.q_lock:
            log.debug('main: adding None request')
            self.queue.insert(-1, None)
        log.debug('main: releasing...')
        self.semaphore.release()
        log.debug('main: joining...')
        self.thread.join()
    
    def run(self):
        """ Main thread loop for the forked thread.
        """
        log.debug('thread: running...')
        while True:
            log.debug('thread: acquiring...')
            self.semaphore.acquire()
            log.debug('thread: acquired. reading request...')
            while True:
                with self.q_lock:
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
    #
