from pathlib import Path
from quivilib.model.image import get_supported_extensions as get_supported_image_extensions


supported_extensions = []
def get_supported_extensions():
    return ['.rar', '.zip', '.cbr', '.cbz']
supported_extensions = get_supported_extensions()


class UnsupportedPathError(Exception):
    pass


class Item(object):
    def __init__(self, path, last_modified=None, chktyp = True, data=None):
        """Create a Item.
        
        @param path: the item path
        @chktyp: check type flag. If false, won't try to poke it to check
            if it is a file or a directory, which could raise errors
            with virtual paths in compressed files. Instead, will consider
            paths ending in slash as directories, otherwise files.
        """ 
        #TODO: (2,1) Test: Check how symlinks and junctions are handled
        self.path = path
        self.last_modified = last_modified
        self.data = data
        if not isinstance(path, Path):
            print(repr(path), type(path))
            assert False, "non-path given to " + __file__
        if path.name == '..':
            self.typ = ItemType.PARENT
            self.ext = ''
            self.namebase = '..'
        elif (chktyp and path.is_file()) or (not chktyp and path.name not in '/\\'):
            self.ext = path.suffix.lower()
            self.namebase = self.path.stem.lower()
            if self.ext.lower() in get_supported_extensions():
                self.typ = ItemType.COMPRESSED
            elif self.ext.lower() in get_supported_image_extensions():
                self.typ = ItemType.IMAGE
            else:
                raise UnsupportedPathError()
        else:
            if not chktyp and path.name in '/\\':
                self.path = Path(self.path[:-1]) 
            #TODO: (2,2) Test: check if it's really correct to default to directory
            self.typ = ItemType.DIRECTORY
            self.ext = ''
            self.namebase = self.path.name

    def __getattr__(self, name):
        #Allow path functions to be called within this class
        #(pseudo-inheritance)
        return getattr(self.path, name)
    
    def __eq__(self, other):
        return other and self.path == other
    
    def __ne__(self, other):
        return not self.__eq__(other)
    
    def __str__(self):
        return str(self.path)
    __repr__ = __str__


class SortOrder(object):
    (NAME,
     EXTENSION,
     TYPE,
     LAST_MODIFIED) = list(range(4))

class ItemType():
    (PARENT,
     DIRECTORY,
     IMAGE,
     COMPRESSED,
     ) = list(range(4))
