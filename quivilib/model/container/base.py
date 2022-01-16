

from quivilib.model.container import Item
from quivilib.model.container import SortOrder
from quivilib.model.container import UnsupportedPathError
from quivilib.util import alphanum_key

import operator

from pubsub import pub as Publisher

#Check if Windows sort is available, by trying to calling it.
#TODO: Replace with the python module natsort. Then finish removing cmpfunc
try:
    #from quivilib.windows.util import logical_cmp
    #logical_cmp('dummy', 'dummy')
    #wincmpfn = logical_cmp
    wincmpfn = None
except:
    wincmpfn = None


class BaseContainer(object):
    def __init__(self, sort_order, show_hidden):
        self._selected_item = None
        self.items = []
        self._sort_order = sort_order
        self.show_hidden = show_hidden
        self.refresh(show_hidden)
        
    def get_sort_order(self):
        return self._sort_order
    
    def set_sort_order(self, order):
        if order == SortOrder.NAME:
            #TODO: (3,2) Improve: should show directories first?
            if wincmpfn:
                keyfn = operator.attrgetter('path', 'ext')
                def cmpfn(a, b):
                    return cmp((wincmpfn(a[0], b[0]), wincmpfn(a[1], b[1])),
                               (0, 0))
            else:
                def keyfn(elem):
                    return alphanum_key(elem.namebase), alphanum_key(elem.ext)
                cmpfn = None
        elif order == SortOrder.TYPE:
            if wincmpfn:
                keyfn = operator.attrgetter('typ', 'path', 'ext')
                def cmpfn(a, b):
                    return cmp((cmp(a[0], b[0]),
                                wincmpfn(a[1], b[1]),
                                wincmpfn(a[2], b[2])),
                               (0, 0, 0))
            else:
                def keyfn(elem):
                    return elem.typ, alphanum_key(elem.namebase), alphanum_key(elem.ext)
                cmpfn = None
        elif order == SortOrder.EXTENSION:
            if wincmpfn:
                keyfn = operator.attrgetter('ext', 'path')
                def cmpfn(a, b):
                    return cmp((wincmpfn(a[0], b[0]), wincmpfn(a[1], b[1])),
                               (0, 0))
            else:
                def keyfn(elem):
                    return alphanum_key(elem.ext), alphanum_key(elem.namebase)
                cmpfn = None
        elif order == SortOrder.LAST_MODIFIED:
            keyfn = operator.attrgetter('typ', 'last_modified')
            cmpfn = None
        else:
            assert False, 'Invalid sort order specified'
        parent = None
        if self.items[0].path == '..':
            parent = self.items.pop(0)
        self.items.sort(key=keyfn)
        if parent:
            self.items.insert(0, parent)
        self._sort_order = order
        Publisher.sendMessage('container.changed', container=self)
        
    sort_order = property(get_sort_order, set_sort_order)
    
    def open_container(self, item_index):
        #Import here to avoid circular import
        from quivilib.model.container.directory import DirectoryContainer
        from quivilib.model.container.compressed import CompressedContainer
        item = self.items[item_index]
        assert item.typ != Item.IMAGE
        if item.typ == Item.PARENT:
            return self.open_parent()
        elif item.typ == Item.DIRECTORY:
            return DirectoryContainer(item.path, self._sort_order, self.show_hidden)
        elif item.typ == Item.COMPRESSED:
            return CompressedContainer(item.path, self._sort_order, self.show_hidden)
        else:
            assert False, 'Invalid container type specified'
            
    def refresh(self, show_hidden):
        self.show_hidden = show_hidden
        paths = self._list_paths()
        self.items = []
        old_selected_item = self._selected_item
        self._selected_item = None
        selected_item = None
        for path, last_modified, data in paths:
            try:
                item = Item(path, last_modified, not self.virtual_files, data)
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
            if self.selected_item.typ == Item.IMAGE:
                Publisher.sendMessage('container.item.changed', index=self.items.index(self.selected_item))
        
    @property
    def item_count(self):
        return len(self.items)

    def get_item_name(self, item_index):
        path = self.items[item_index]
        if not path.name and path.drive:
            return path.drive
        return path.name
    
    def get_item_extension(self, item_index):
        ext = self.items[item_index].ext
        if ext and ext[0] == '.':
            return ext[1:]
        return ext
    
    def get_item_path(self, item_index):
        return self.items[item_index].path
    
    def get_item_last_modified(self, item_index):
        return self.items[item_index].last_modified
    
    def set_selected_item(self, item):
        old_selected_item = self._selected_item
        if isinstance(item, int):
            self._selected_item = self.items[item]
        elif isinstance(item, str):
            lst = [i for i in self.items if i.path == item]
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
        try:
            return self.items.index(self._selected_item)
        except ValueError:
            return -1 
    
    selected_item = property(get_selected_item, set_selected_item)
    
    @property
    def virtual_files(self):
        return False
    
    def can_delete(self):
        raise NotImplementedError()
    
    @property
    def universal_path(self):
        raise NotImplementedError()
    
    def open_parent(self):
        raise NotImplementedError()
    
    def open_image(self, item_index):
        raise NotImplementedError()
    
    def _list_paths(self, show_hidden):
        raise NotImplementedError()

