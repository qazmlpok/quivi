from pubsub import pub as Publisher




class DebugController(object):
    def __init__(self, control):
        self.control = control
        #self.model = model
        #Subscribe to cache events.
        #Messages will be handled even if the window isn't open.
        #Publisher.subscribe(self.on_queue_change, 'debug.queue_changed')
        #Publisher.subscribe(self.on_cache_change, 'debug.cache_changed')
        
        #Is there an easy way to put all the list item stuff here?
        self.queue_data = {}
        
    def open_debug_cache_dialog(self):
        #Currently no parameters.
        Publisher.sendMessage('debug.open_cache_dialog', params=None)

    def open_debug_memory_dialog(self):
        #Currently no parameters.
        Publisher.sendMessage('debug.open_memory_dialog', params=None)
