

from pathlib import Path

from wx.lib.pubsub import pub as Publisher



CONFIG_KEY = 'Favorites'


#TODO: Verify it's truly safe to just use the pathlib obj directly
#I'm assuming the thirdparty module just didn't support this, hence the .lower
class Favorites(object):
    def __init__(self, config=None):
        self._favorites = {}
        if config:
            self.load(config)
        Publisher.subscribe(self.on_container_opened, 'container.opened')
        
    def insert(self, path):
        #self._favorites[path.lower()] = path
        self._favorites[path] = path
        
    def remove(self, path):
        #lpath = path.lower()
        #if lpath in self._favorites:
        #    del self._favorites[lpath]
        del self._favorites[path]
        
    def contains(self, path):
        #return path.lower() in self._favorites
        return path in self._favorites
    
    def load(self, config):
        if config.has_section(CONFIG_KEY):
            items = config.items(CONFIG_KEY)
            for key, value in items:
                path = Path(value)
                self.insert(path)
                    
    def save(self, config):
        if config.has_section(CONFIG_KEY):
            config.remove_section(CONFIG_KEY)
        config.add_section(CONFIG_KEY)
        for index, path in enumerate(self._favorites.values()):
            config.set(CONFIG_KEY, str(index), path)
            
    def getitems(self):
        #TODO: (1,2) Improve: use human sort
        return sorted((key, value) for key, value in list(self._favorites.items()))
    
    def on_container_opened(self, message):
        container = message.data
        favorite = self.contains(container.path)
        Publisher.sendMessage('favorite.opened', favorite)
    