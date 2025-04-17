from pathlib import Path

from pubsub import pub as Publisher

CONFIG_KEY = 'SavedPaths'

#(Much of this is copied from favorites)

class SavedPaths(object):
    def __init__(self, config=None):
        self._paths = []
        if config:
            self.load(config)
    
    def load(self, config):
        if config.has_section(CONFIG_KEY):
            items = config.items(CONFIG_KEY)
            for key, value in items:
                p = SavedPath.deserialize(value)
                self.insert(p)

    def save(self, config):
        if config.has_section(CONFIG_KEY):
            config.remove_section(CONFIG_KEY)
        config.add_section(CONFIG_KEY)
        for index, p in enumerate(self._paths):
            config.set(CONFIG_KEY, str(index), p.serialize())

    def insert(self, fav):
        self._paths.append(fav)
    def add_new(self, name, path):
        path = Path(path)
        self.insert(SavedPath(name, path))
    
    def count(self):
        return len(self._paths)
        
    def __iter__(self):
        for elem in self._paths:
            yield (elem.name, elem.path)
    
    def path_already_exists(self, testpath):
        """ Determine if the provided path already exists in settings.
        Normalization is just what is provided by pathlib
        """
        testpath = Path(testpath)
        lookup = {x.path: 1 for x in self._paths}
        return testpath in lookup
    def path_is_valid(self, testname, testpath):
        return not ('|' in testname or '|' in testpath)

class SavedPath:
    def __init__(self, name, path):
        self.name = name
        self.path = path

    def serialize(self):
        """
        Convert to a string for saving in configparser, which doesn't support complex objects.
        This could be done as JSON but I don't want to throw in the dependency for something so small.
        """
        return f'[{self.name}|{self.path}]'

    @staticmethod
    def deserialize(input):
        """Opposite of serialize. Returns a new instance from a string.
        """
        name = None
        path = None
        #| is used as a separator because it shouldn't appear in a path. It can, but it shouldn't.
        #The GUI will reject names/paths that contain a | as an additional protection.
        if (input[0] == '[' and '|' in input):
            (name, path) = input.strip("[]").split('|')
        else:
            #Throw? Silently drop the invalid record?
            return None
        path = Path(path)
        
        return SavedPath(name, path)
        
    def __repr__(self):
        return str(self.path)
        
    def __hash__(self):
        return hash(self.getKey())
    def __eq__(self, other):
        return isinstance(other, self.__class__) and self.path == other.path and self.name == other.name
        
    def __lt__(self, other):
        return str(self) < str(other)
    def __le__(self, other):
        return str(self) <= str(other)
        
    def getKey(self):
        return (self.path, self.page is not None)
