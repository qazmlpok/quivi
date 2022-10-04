

from quivilib.i18n import _
from quivilib import meta
from quivilib.model.container import Item
from quivilib.model.container import get_supported_extensions as get_supported_container_extensions
from quivilib.model.container.directory import DirectoryContainer
from quivilib.model.container.compressed import CompressedContainer
from quivilib.model.image import get_supported_extensions as get_supported_image_extensions
from quivilib.control.cache import ImageCacheLoadRequest
from pathlib import Path

from pubsub import pub as Publisher
from quivilib.meta import PATH_SEP
import wx

import sys
import logging
log = logging.getLogger('control.file_list')


def _need_delete_confirmation():
    #No confirmation on win32 because it uses the recycle bin.
    return (sys.platform != 'win32')

def _ask_delete_confirmation(window, path):
    dlg = wx.MessageDialog(window, _('Are you sure you want to delete "%s"?') % path.name,
                           _("Confirm file deletion"), wx.YES_NO | wx.ICON_QUESTION)
    res = dlg.ShowModal()
    dlg.Destroy()
    return res

def _delete_file(path, window=None):
    if sys.platform == 'win32':
        #Use win32com.shell to send the file to the recycle bin, rather than outright deleting it.
        from quivilib.windows.util import delete_file
        delete_file(str(path), window)
    else:
        path.unlink()

def _ask_delete_favorite(window, path):
    dlg = wx.MessageDialog(window, _('''The file or directory "%s" couldn't be found. Remove the favorite?''') % path.name,
                           _("Favorite not found"), wx.YES_NO | wx.ICON_QUESTION)
    res = dlg.ShowModal()
    dlg.Destroy()
    return res

class FileListController(object):
    def __init__(self, model, start_container):
        self.model = model
        Publisher.subscribe(self.on_file_list_activated, 'file_list.activated')
        Publisher.subscribe(self.on_file_list_selected, 'file_list.selected')
        Publisher.subscribe(self.on_file_list_column_clicked, 'file_list.column_clicked')
        Publisher.subscribe(self.on_file_list_begin_drag, 'file_list.begin_drag')
        Publisher.subscribe(self.on_favorite_open, 'favorite.open')
        Publisher.subscribe(self.on_container_item_changed, 'container.item.changed')
        Publisher.subscribe(self.on_cache_image_loaded, 'cache.image_loaded')
        Publisher.subscribe(self.on_cache_image_load_error, 'cache.image_load_error')
        Publisher.subscribe(self.on_file_dropped, 'file.dropped')
        self.pending_request = None
        self._last_opened_item = None
        self._direction = 1
        self.show_hidden = False
        self._set_container(start_container)
        
    def on_file_list_activated(self, *, index):
        container = self.model.container
        if container.items[index].typ != Item.IMAGE:
            opened = container.open_container(index)
            if opened:
                self._set_container(opened)
            
    def on_file_list_selected(self, *, index):
        container = self.model.container
        container.selected_item = index
        if container.items[index].typ == Item.IMAGE:
            self.open_item(index)
            
    def on_file_list_column_clicked(self, *, sort_order):
        self.model.container.sort_order = sort_order
        
    def on_file_list_begin_drag(self, *, obj):
        if self.model.container.virtual_files == False:
            obj.path = self.model.container.get_item_path(obj.idx)
        else:
            obj.path = None
            
    def on_container_item_changed(self, *, index):
        self.open_item(index)
        
    def on_favorite_open(self, *, favorite, window=None):
        try:
            is_placeholder = favorite.page is not None
            self.open_path(favorite.path, is_placeholder)
            if is_placeholder:
                #Bypass the default page open and manually select the saved index.
                #Otherwise it will try to load the cover page and the selected page.
                self.select_index(int(favorite.page))
        except FileNotFoundError as e:
            #Favorite invalid; probably deleted manually. Prompt user to remove.
            if _ask_delete_favorite(window, path) == wx.ID_YES:
                #Duplicate of remove_favorite in main.
                self.model.favorites.remove(path)
                Publisher.sendMessage('favorites.changed', favorites=self.model.favorites)
                Publisher.sendMessage('favorite.opened', favorite=False)
                

    def open_item(self, item_index):
        container = self.model.container
        item = container.items[item_index]
        if item.typ == Item.IMAGE:
            Publisher.sendMessage('busy', busy=True)
            if meta.CACHE_ENABLED:
                request = ImageCacheLoadRequest(container, item, self.model.canvas.view)
                self.pending_request = request
                Publisher.sendMessage('container.image.loading', item=container.items[item_index])
                Publisher.sendMessage('cache.clear_pending', request=request)
                log.debug(f"fl: requesting cache for {item_index}")
                Publisher.sendMessage('cache.load_image', request=request)
                log.debug("fl: cache requested")
                if self._last_opened_item is None or item_index >= self._last_opened_item:
                    self._direction = 1
                else:
                    self._direction = -1
                for i in range(meta.PREFETCH_COUNT):
                    idx = item_index + ((i + 1) * self._direction)
                    if idx > 0 and idx < len(container.items) and container.items[idx].typ == Item.IMAGE:
                        request = ImageCacheLoadRequest(container, container.items[idx], self.model.canvas.view)
                        log.debug(f"fl: requesting prefetch of {idx}")
                        Publisher.sendMessage('cache.load_image', request=request)
                        log.debug("fl: prefetch requested")
                log.debug("fl: done")
            else:
                path = container.items[item_index].path
                f = container.open_image(item_index)
                #can't use "with" because not every file-like object used here supports it
                try:
                    self.model.canvas.load(f, path)
                finally:
                    f.close()
                Publisher.sendMessage('busy', busy=False)
                Publisher.sendMessage('container.image.opened', item=container.items[item_index])
            self._last_opened_item = item_index
        else:
            opened = self.model.container.open_container(item_index)
            if opened:
                self._set_container(opened)
                
    def on_cache_image_loaded(self, *, request):
        if request == self.pending_request:
            self.pending_request = None
            self.model.canvas.load_img(request.img)
            Publisher.sendMessage('busy', busy=False)
            item = request.item
            Publisher.sendMessage('container.image.opened', item=item)
        
    def on_cache_image_load_error(self, *, request, exception, tb):
        if request == self.pending_request:
            Publisher.sendMessage('busy', busy=False)
            Publisher.sendMessage('error', exception=exception, tb=tb)
            
    def on_file_dropped(self, *, path):
        self.open_path(path)

    def open_parent(self):
        container = self.model.container
        parent = container.open_parent()
        if parent:
            self._set_container(parent)

    def open_directory(self):
        class Request():
            start_directory = self.model.container.path
            directory = None
        req = Request()
        Publisher.sendMessage('file_list.open_directory_dialog', req=req)
        if req.directory:
            self.open_path(req.directory)
    
    def select_index(self, nindex):
        container = self.model.container
        #Notice that it works even if no item is selected (item = -1)
        if 0 <= nindex < container.item_count:
            container.selected_item = nindex
            if container.items[nindex].typ == Item.IMAGE:
                self.open_item(nindex)
    
    def select_next(self, skip):
        container = self.model.container
        nindex = container.selected_item_index + skip
        self.select_index(nindex)

    def open_selected_container(self):
        container = self.model.container
        index = container.selected_item_index
        if container.items[index].typ != Item.IMAGE:
            container = container.open_container(index)
            self._set_container(container)
            
    def open_sibling(self, skip):
        Publisher.sendMessage('gui.freeze')
        try:
            container = self.model.container
            parent = container.open_parent()
            if parent:
                self.model.container = parent
                nindex = parent.selected_item_index + skip
                if 0 <= nindex < parent.item_count:
                    self.open_item(nindex)
                    if parent.items[nindex].typ == Item.IMAGE:
                        parent.selected_item = nindex
        finally:
            Publisher.sendMessage('gui.thaw') 
        
    def refresh(self):
        Publisher.sendMessage('cache.flush')
        self.model.container.refresh(self.show_hidden)
        
    def _refresh_after_delete(self, deleted_index):
        container = self.model.container
        self.refresh()
        nindex = deleted_index if self._direction == 1 else deleted_index - 1
        if nindex < 0:
            nindex = 0
        if nindex >= len(container.items):
            nindex = len(container.items) - 1
        container.selected_item = nindex 
        if container.items[nindex].typ == Item.IMAGE:
            self.open_item(nindex)
        
    def delete(self, window=None):
        img = self.model.canvas.img
        if not self._can_delete():
            return
        index = self.model.container.selected_item_index
        path = self.model.container.items[index].path
        type = self.model.container.items[index].typ
        if _need_delete_confirmation():
            if _ask_delete_confirmation(window, path) == wx.ID_NO:
                return
        #Release any handle on the file...
        if type == Item.IMAGE and img:
            img.close()
        _delete_file(path, window)
        self._refresh_after_delete(index)
    
    def on_update_delete_menu_item(self, event):
        event.Enable(self._can_delete())
        
    def _can_delete(self):
        can_delete = False
        container = self.model.container
        if container.can_delete():
            index = container.selected_item_index
            if index != -1:
                if container.items[index].typ in (Item.IMAGE, Item.COMPRESSED):
                    can_delete = True
        return can_delete
        
    def open_path(self, path, skip_open=False):
        sort_order = self.model.container.sort_order
        show_hidden = self.model.container.show_hidden
        
        if path.is_dir():
            container = DirectoryContainer(path, sort_order, show_hidden)
            self._set_container(container, skip_open)
        elif path.is_file() and path.suffix.lower() in get_supported_image_extensions():
            container = DirectoryContainer(path.parent, sort_order, show_hidden)
            self.model.container = container
            container.selected_item = path
            if container.selected_item_index != -1:
                self.open_item(container.selected_item_index)
        elif path.is_file() and path.suffix.lower() in get_supported_container_extensions():
            container = CompressedContainer(path, sort_order, show_hidden)
            self._set_container(container, skip_open)
        else:
            paths = str(path).split(PATH_SEP)
            root_container_path = Path(paths[0])
            if root_container_path.is_file():
                root_container = CompressedContainer(root_container_path, sort_order, show_hidden)
                container = self._open_virtual_path(root_container, paths[1:])
                if container.selected_item_index == -1:
                    self._set_container(container, skip_open)
                else:
                    self.model.container = container
                    self.open_item(container.selected_item_index)
            else:
                raise FileNotFoundError(_('File or directory does not exist'))
            
    def toggle_show_hidden(self):
        self.show_hidden = not self.show_hidden
        self.refresh()
        
    def on_update_hidden_menu_item(self, event):
        event.Check(self.show_hidden)
        
    def _open_virtual_path(self, container, paths):
        if not paths:
            return container
        path = Path(paths[0])
        container.selected_item = path
        if container.selected_item_index == -1:
            return container
        else:
            if container.selected_item.typ == Item.IMAGE:
                return container
            else:
                container = container.open_container(container.selected_item_index)
                return self._open_virtual_path(container, paths[1:])
        
    def _set_container(self, container, skip_open=False):
        if self.model.container is not None:
            self.model.container.close_container()
        self.model.container = container
        self._last_opened_item = None
        if not skip_open:
            for idx, item in enumerate(self.model.container.items):
                if item.typ == Item.IMAGE:
                    if self.model.settings.getint('Options', 'OpenFirst') and self.model.container.selected_item_index == -1:
                        self.model.container.selected_item = idx
                        self.open_item(idx)
                    else:
                        request = ImageCacheLoadRequest(self.model.container, item, self.model.canvas.view)
                        log.debug("fl: requesting prefetch of first image in container...")
                        Publisher.sendMessage('cache.load_image', request=request)
                    break
        if self.model.settings.getint('Options', 'OpenFirst') and self.model.container.selected_item_index == -1:
            idx = -1
            if len(self.model.container.items) > 0:
                idx = 0
                if self.model.container.items[0].typ == Item.PARENT:
                    if len(self.model.container.items) > 1:
                        idx = 1
            if idx != -1:
                self.model.container.selected_item = idx
