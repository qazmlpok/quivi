import os
import sys
from datetime import datetime
from pathlib import Path
from pubsub import pub as Publisher

from quivilib.model.container.base import BaseContainer
from quivilib.model.container.root import RootContainer

from typing import IO


def _is_hidden(path):
    if sys.platform == 'win32':
        import win32api
        import win32con
        try:
            flags = win32api.GetFileAttributes(path)
            if flags & win32con.FILE_ATTRIBUTE_HIDDEN:
                return True
        except:
            pass
    elif path.name.startswith('.'):
        return True
    return False


class DirectoryContainer(BaseContainer):
    def __init__(self, directory, sort_order, show_hidden) -> None:
        self.path = directory.resolve()
        BaseContainer.__init__(self, sort_order, show_hidden)
        Publisher.sendMessage('container.opened', container=self)
                
    def _list_paths(self):
        paths = []
        for path in self.path.iterdir():
            last_modified = None
            if not self.show_hidden and _is_hidden(path):
                continue
            try:
                #TODO: (2,2) Fix: on Windows, dates can be pre-1970
                last_modified = datetime.fromtimestamp(path.lstat().st_mtime)
            except (ValueError, os.error):
                pass
            data = None
            paths.append((path, last_modified, data))
        paths.insert(0, (Path('..'), None, None))
        return paths
            
    @property
    def name(self):
        name = self.path.name
        if name == '':
            if self.path.drive != '':
                return self.path.drive
            else:
                return '/'
        return self.path.name
       
    def open_parent(self) -> BaseContainer:
        parent: BaseContainer
        p = self.path.parent
        if p == self.path and p.drive != '':
            #The parent is the root, and drives exists
            parent = RootContainer(self.sort_order, self.show_hidden)
        else:
            parent = DirectoryContainer(self.path.parent, self._sort_order, self.show_hidden)
        parent.selected_item = self.path
        return parent
    
    def open_image(self, item_index: int) -> IO[bytes]:
        img = self.items[item_index].path.open('rb')
        return img
    
    def can_delete(self) -> bool:
        return True
    
    @property
    def universal_path(self) -> Path|None:
        return self.path
