from datetime import datetime
from pathlib import Path
import operator

from pubsub import pub as Publisher
from natsort import natsort_keygen, ns

from quivilib.model.container import Item, ItemType, SortOrder
from quivilib.model.container import UnsupportedPathError

from typing import List, IO, Tuple

class BaseContainer(object):
    def __init__(self, sort_order: SortOrder, show_hidden: bool) -> None:
        self._selected_item: Item|None = None
        self.items: List[Item] = []
        self._sort_order = sort_order
        self.show_hidden = show_hidden
        self.refresh(show_hidden)
        
    def get_sort_order(self) -> SortOrder:
        return self._sort_order
    
    def set_sort_order(self, order: SortOrder) -> None:
        if order == SortOrder.NAME:
            def keyfn(elem):
                return str(elem.path)
        elif order == SortOrder.TYPE:
            def keyfn(elem):
                return elem.typ, str(elem.path)
        elif order == SortOrder.EXTENSION:
            def keyfn(elem):
                return elem.ext, elem.namebase
        elif order == SortOrder.LAST_MODIFIED:
            keyfn = operator.attrgetter('typ', 'last_modified')
        else:
            assert False, 'Invalid sort order specified'
        parent = None
        if self.items[0].path.name == '..':
            parent = self.items.pop(0)
        natsort_key = natsort_keygen(key=keyfn, alg=ns.PATH)
        self.items.sort(key=natsort_key)
        if parent:
            self.items.insert(0, parent)
        self._sort_order = order
        Publisher.sendMessage('container.changed', container=self)
        
    sort_order = property(get_sort_order, set_sort_order)
    
    def open_container(self, item_index: int) -> 'BaseContainer':
        #Import here to avoid circular import
        from quivilib.model.container.directory import DirectoryContainer
        from quivilib.model.container.compressed import CompressedContainer
        item = self.items[item_index]
        assert item.typ != ItemType.IMAGE
        if item.typ == ItemType.PARENT:
            return self.open_parent()
        elif item.typ == ItemType.DIRECTORY:
            return DirectoryContainer(item.path, self._sort_order, self.show_hidden)
        elif item.typ == ItemType.COMPRESSED:
            return CompressedContainer(item.path, self._sort_order, self.show_hidden)
        else:
            assert False, 'Invalid container type specified'

    def close_container(self) -> None:
        pass

    def refresh(self, show_hidden: bool) -> None:
        self.show_hidden = show_hidden
        paths = self._list_paths()
        self.items = []
        old_selected_item = self._selected_item
        self._selected_item = None
        selected_item = None
        for path, last_modified in paths:
            try:
                item = Item(path, last_modified, not self.virtual_files, None)
                self.items.append(item)
            except UnsupportedPathError:
                continue
            if old_selected_item == item:
                selected_item = self.items[-1]
            #TODO: (2,3) Test: check is exceptions can be thrown inside the loop
        
        #Fill aditional item info
        for idx, item in enumerate(self.items):
            item.full_path = self.get_item_path(idx)
        
        self.set_sort_order(self._sort_order)
        if selected_item:
            #TODO: (1,4) Improve: check if item has really changed before sending message?
            #i.e., file has been modified (but it's probably overkill)
            self.selected_item = selected_item
            if self.selected_item.typ == ItemType.IMAGE:
                Publisher.sendMessage('container.item.changed', index=self.items.index(self.selected_item))

    @property
    def item_count(self):
        return len(self.items)

    def get_item_name(self, item_index):
        path = self.items[item_index]
        if not path.name and path.drive:
            return path.drive
        return path.name
    
    def get_item_extension(self, item_index: int) -> str:
        ext = self.items[item_index].ext
        if ext and ext[0] == '.':
            return ext[1:]
        return ext
    
    def get_item_path(self, item_index: int) -> Path:
        return self.items[item_index].path
    
    def get_item_last_modified(self, item_index):
        return self.items[item_index].last_modified
    
    def set_selected_item(self, item: int|Path|Item) -> None:
        old_selected_item = self._selected_item
        if isinstance(item, int):
            self._selected_item = self.items[item]
        elif isinstance(item, Path):
            lst = [i for i in self.items if i.path.name == item.name]
            if lst:
                self._selected_item = lst[0]
        else:
            if item in self.items:
                self._selected_item = item
            else:
                raise RuntimeError("Invalid item set as selected")
        if self._selected_item and self._selected_item != old_selected_item:
            idx = self.items.index(self._selected_item)
            Publisher.sendMessage('container.selection_changed', idx=idx, item=self._selected_item)
            
    def get_selected_item(self):
        return self._selected_item

    @property
    def selected_item_index(self):
        if self._selected_item is None:
            return -1
        try:
            return self.items.index(self._selected_item)
        except ValueError:
            return -1 
    
    selected_item = property(get_selected_item, set_selected_item)
    
    @property
    def virtual_files(self):
        return False
    
    def can_delete(self) -> bool:
        raise NotImplementedError()
    
    @property
    def universal_path(self) -> Path|None:
        raise NotImplementedError()
    
    def open_parent(self) -> 'BaseContainer':
        raise NotImplementedError()
    
    def open_image(self, item_index: int) -> IO[bytes]:
        raise NotImplementedError()
    
    def _list_paths(self) -> List[Tuple[Path, datetime|None]]:
        raise NotImplementedError()
