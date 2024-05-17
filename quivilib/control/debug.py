from pubsub import pub as Publisher




class DebugController(object):
    def __init__(self, control):
        self.control = control
        #self.model = model
        #Subscribe to cache events.
        #Publisher.subscribe(self.on_cache_image_loaded, 'cache.image_loaded')
        #Publisher.subscribe(self.on_cache_image_load_error, 'cache.image_load_error')
        
    def open_debug_cache_dialog(self):
        #Currently no parameters.
        Publisher.sendMessage('debug.open_cache_dialog', params=None)
