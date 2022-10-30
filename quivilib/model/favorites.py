

from pathlib import Path

from pubsub import pub as Publisher
from quivilib.meta import PATH_SEP


CONFIG_KEY = 'Favorites'

class Favorites(object):
    def __init__(self, config=None):
        self._favorites = {}
        #Maintains the order within the configuration, which should always be by date
        #(Or I could just add a date to everything)
        self._ordered = []
        if config:
            self.load(config)
        Publisher.subscribe(self.on_container_opened, 'container.opened')
        
    def insert(self, fav):
        self._favorites[fav.getKey()] = fav
        self._ordered.append(fav)
        
    def remove(self, path, is_placeholder=False):
        del self._favorites[(path, is_placeholder)]
        for fav in self._ordered:
            if str(fav.path) == str(path) and fav.is_placeholder() == is_placeholder:
                self._ordered.remove(fav)
        
    def contains(self, path):
        return path in self._favorites
    
    def load(self, config):
        if config.has_section(CONFIG_KEY):
            items = config.items(CONFIG_KEY)
            for key, value in items:
                fav = Favorite.deserialize(value)
                self.insert(fav)

    def save(self, config):
        if config.has_section(CONFIG_KEY):
            config.remove_section(CONFIG_KEY)
        config.add_section(CONFIG_KEY)
        for index, fav in enumerate(self._favorites.values()):
            config.set(CONFIG_KEY, str(index), fav.serialize())
            
    def getitems(self):
        #TODO: (1,2) Improve: use human sort
        return sorted((key, value) for key, value in list(self._favorites.items()))
    
    def ordered_items(self):
        return self._ordered
    
    def on_container_opened(self, *, container):
        favorite = self.contains(container.path)
        Publisher.sendMessage('favorite.opened', favorite=favorite)
    
class Favorite:
    def __init__(self, path, page, display):
        self.page = page
        self.display = display
        self.path = path
    
    def displayText(self):
        """
        Format the favorite/placeholder for display in the menu.
        """
        if not self.path:
            return None
        #In path for drives (e.g. D:\), name is '' 
        if self.path.name == '':
            name = str(self.path)
        else:
            name = self.path.name
        #Handle universal path names
        name = name.split(PATH_SEP)[-1]
        #Prevents incorrect shortcut definition
        name = name.replace('&', '&&')
        
        if self.display is not None:
            #Or page number? Which is better?
            name += ", " + self.display
        
        return name
        
    def is_placeholder(self):
        return self.page is not None
        
    def serialize(self):
        """
        Turns a favorite or placeholder into a string that can be saved to the config
        This could be done as JSON but I don't want to throw in the dependency for something so small.
        """
        if self.page is None:
            return str(self.path)
        return f'[{self.page}|{self.path}|{self.display}]'
    
    @staticmethod
    def deserialize(input):
        """
        Opposite of serialize. Returns a new instance from a string.
        """
        page = None
        display = None
        #Probably not the best approach, but config doesn't appear to support lists.
        #If the first character is [, treat it as a list containing 3 values for Placeholders.
        #| is used as a separator because it shouldn't appear in a path. It can, but it shouldn't.
        if (input[0] == '['):
            (page, path, display, *_) = input.strip("[]").split('|') + [None] * 3
        else:
            path = input
        path = Path(path)
        
        return Favorite(path, page, display)

    def __repr__(self):
        return str(self.path)
        
    def __hash__(self):
        return hash(self.getKey())
        
    def __eq__(self, other):
        #return isinstance(other, self.__class__) and self.path == other.path and self.page == other.page
        #All placeholders for the same path are equal; this results in only a single placeholder for a given container.
        return isinstance(other, self.__class__) and self.path == other.path and (self.page is None) == (other.page is None)
    def __lt__(self, other):
        return str(self) < str(other)
    def __le__(self, other):
        return str(self) <= str(other)
        
    def getKey(self):
        return (self.path, self.page is not None)
