import os, sys
from pathlib import Path
import logging

from pubsub import pub as Publisher
import wx

from quivilib.i18n import _
from quivilib import meta
from quivilib.model.container import Item, ItemType
from quivilib.model.container import get_supported_extensions as get_supported_container_extensions
from quivilib.model.container.directory import DirectoryContainer
from quivilib.model.container.compressed import CompressedContainer
from quivilib.model.image import get_supported_extensions as get_supported_image_extensions
from quivilib.control.cache import ImageCacheLoadRequest
from quivilib.meta import PATH_SEP
from quivilib.util import DebugTimer

log = logging.getLogger('control.file_list')


def _need_delete_confirmation():
    #No confirmation on win32 because it uses the recycle bin.
    return (sys.platform != 'win32')

def _ask_delete_confirmation(window, path):
    if not _need_delete_confirmation():
        return True
    dlg = wx.MessageDialog(window, _('Are you sure you want to delete "%s"?') % path.name,
                           _("Confirm file deletion"), wx.YES_NO | wx.ICON_QUESTION)
    res = dlg.ShowModal()
    dlg.Destroy()
    return res == wx.ID_YES

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
        Publisher.subscribe(self.on_file_dropped, 'file.dropped')
        Publisher.subscribe(self.on_move_file, 'file_list.move_file')
        self.pending_request = None
        self._last_opened_item = None
        self._direction = 1
        self.show_hidden = False
        self._set_container(start_container)
        
    def on_file_list_activated(self, *, index):
        container = self.model.container
        if container.items[index].typ != ItemType.IMAGE:
            opened = container.open_container(index)
            if opened:
                self._set_container(opened)
            
    def on_file_list_selected(self, *, index):
        container = self.model.container
        container.selected_item = index
        if container.items[index].typ == ItemType.IMAGE:
            self.open_item(index)
            
    def on_file_list_column_clicked(self, *, sort_order):
        self.model.container.sort_order = sort_order
        
    def on_file_list_begin_drag(self, *, obj):
        if not self.model.container.virtual_files:
            obj.path = self.model.container.get_item_path(obj.idx)
        else:
            obj.path = None
            
    def on_container_item_changed(self, *, index):
        self.open_item(index)

    def on_favorite_open(self, *, favorite, window=None):
        try:
            is_placeholder = favorite.page is not None
            self._open_path(favorite.path, is_placeholder)
            if is_placeholder:
                #Bypass the default page open and manually select the saved index.
                #Otherwise it will try to load the cover page and the selected page.
                #TODO: Would calling open_path on the direct image work better?
                self.select_index(int(favorite.page))
                autodelete = self.model.settings.get('Options', 'PlaceholderDelete') == '1'
                if autodelete:
                    self.model.favorites.remove(favorite.path, is_placeholder)
                    Publisher.sendMessage('favorites.changed', favorites=self.model.favorites)
                    log.debug(f'Removing placeholder on open: {favorite.path}')
        except FileNotFoundError as e:
            #Favorite invalid; probably deleted manually. Prompt user to remove.
            if _ask_delete_favorite(window, favorite.path) == wx.ID_YES:
                #Duplicate of remove_favorite in main.
                self.model.favorites.remove(favorite.path, is_placeholder)
                Publisher.sendMessage('favorites.changed', favorites=self.model.favorites)
                Publisher.sendMessage('favorite.opened', favorite=False)


    def open_item(self, item_index: int) -> None:
        container = self.model.container
        item = container.items[item_index]
        if item.typ == ItemType.IMAGE:
            log.debug(f"fl: requesting load for {item_index}")
            Publisher.sendMessage('canvas.load.img', container=container, item=item, preload=False)
            #If cache enabled, additionally send preload requests.
            if meta.CACHE_ENABLED:
                if self._last_opened_item is None or item_index >= self._last_opened_item:
                    self._direction = 1
                else:
                    self._direction = -1
                for i in range(meta.PREFETCH_COUNT):
                    idx = item_index + ((i + 1) * self._direction)
                    if idx > 0 and idx < len(container.items) and container.items[idx].typ == ItemType.IMAGE:
                        log.debug(f"fl: requesting cache preload of {idx}")
                        Publisher.sendMessage('canvas.load.img', container=container, item=container.items[idx], preload=True)
                log.debug("fl: done")
            self._last_opened_item = item_index
        else:
            opened = container.open_container(item_index)
            if opened:
                self._set_container(opened)

    def on_file_dropped(self, *, path):
        self.open_path(path)

    def open_parent(self):
        container = self.model.container
        parent = container.open_parent()
        if parent and parent is not container:
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
            if container.items[nindex].typ == ItemType.IMAGE:
                self.open_item(nindex)
    
    def select_next(self, skip):
        container = self.model.container
        nindex = container.selected_item_index + skip
        self.select_index(nindex)

    def open_selected_container(self):
        container = self.model.container
        index = container.selected_item_index
        if container.items[index].typ != ItemType.IMAGE:
            container = container.open_container(index)
            self._set_container(container)
            
    def open_sibling(self, skip):
        Publisher.sendMessage('gui.freeze')
        try:
            container = self.model.container
            parent = container.open_parent()
            if parent and parent is not container:
                self.model.container = parent
                nindex = parent.selected_item_index + skip
                if 0 <= nindex < parent.item_count:
                    self.open_item(nindex)
                    if parent.items[nindex].typ == ItemType.IMAGE:
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
        nindex = max(nindex, 0)
        nindex = min(nindex, len(container.items) - 1)
        container.selected_item = nindex 
        if container.items[nindex].typ == ItemType.IMAGE:
            self.open_item(nindex)
        
    def delete(self, window=None):
        img = self.canvas.get_img()
        if not self._can_delete():
            return
        index = self.model.container.selected_item_index
        path = self.model.container.items[index].path
        filetype = self.model.container.items[index].typ
        if not _ask_delete_confirmation(window, path):
            return
        #Release any handle on the file...
        if filetype == ItemType.IMAGE and img:
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
                if container.items[index].typ in (ItemType.IMAGE, ItemType.COMPRESSED):
                    can_delete = True
        return can_delete

    def on_move_file(self, *, new_dir: Path):
        """ If the opened container is a zipfile, prompt to move it to a new location.
        In theory this could be done for regular dirs too, but this isn't supported.
        """
        if not self._can_move():
            return
        cont = self.model.container
        old_cont = cont
        old_path = cont.path
        filename = old_path.name
        new_path = new_dir / filename
        
        #Basic validation; the UI will check some of these, and `move` should throw if there are other problems
        if (old_path.parent == new_dir):
            raise Exception("The destination and source directories are the same.")
        if not os.path.isdir(new_dir):
            raise Exception(f"The target path '{new_dir}' isn't a directory")
        if os.path.isfile(new_path):
            raise Exception(f"The target path '{new_path}' already exists")
        
        #Preserve
        sort_order = self.model.container.sort_order
        show_hidden = self.model.container.show_hidden
        selection = cont.selected_item_index
        cont.close_container()
        self.model.container = None
        
        #On the same physical drive this is nearly instant; across volumes it's potentially hundreds of ms
        #(longer if the drive has to start up or anything else). It's definitely noticable.
        Publisher.sendMessage('busy', busy=True)
        with DebugTimer(f"move: Moving opened archive to '{new_path}'"):
            import shutil
            shutil.move(old_path, new_path)
        Publisher.sendMessage('busy', busy=False)
        
        #Reopen to the old position.
        #I think _open_path could do everything, including the img re-open but I don't trust that block of code.
        cont = CompressedContainer(new_path, sort_order, show_hidden)
        #This will send an event but it should be harmless.
        cont.set_selected_item(selection)
        self._set_container(cont, True)
        #There _should_ be no need to send messages or open anything.
        
        #The cache is _effectively_ invalidated. This is because a request is the container plus path.
        #Tell the cache to update references to avoid this issue
        Publisher.sendMessage('cache.move_file', old_cont=old_cont, new_cont=cont)
        
    def on_update_move_menu_item(self, event):
        event.Enable(self._can_move())

    def _can_move(self):
        if not self.model.container:
            return False
        return self.model.container.can_move

    def open_path(self, path, skip_open=False):
        #Check if this path is saved as a placeholder. If it is, load it instead
        autoload = self.model.settings.get('Options', 'PlaceholderAutoOpen') == '1'
        if (autoload and self.model.favorites.contains(path, True)):
            favorite = self.model.favorites.getFavorite(path, True)
            self.on_favorite_open(favorite=favorite)
        else:
            self._open_path(path, skip_open)
    def _open_path(self, path, skip_open=False):
        """Open the given path for viewing. This may be a directory (show images), a single image,
        or a archive (e.g. zip) containing images.
        Opening a single image will open the containing directory and jump directly to that image.
        """
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
            if container.selected_item.typ == ItemType.IMAGE:
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
                if item.typ == ItemType.IMAGE:
                    if self.model.settings.getint('Options', 'OpenFirst') and self.model.container.selected_item_index == -1:
                        self.model.container.selected_item = idx
                        self.open_item(idx)
                    else:
                        request = ImageCacheLoadRequest(self.model.container, item)
                        log.debug("fl: requesting prefetch of first image in container...")
                        Publisher.sendMessage('cache.load_image', request=request)
                    break
        if self.model.settings.getint('Options', 'OpenFirst') and self.model.container.selected_item_index == -1:
            idx = -1
            if len(self.model.container.items) > 0:
                idx = 0
                if self.model.container.items[0].typ == ItemType.PARENT:
                    if len(self.model.container.items) > 1:
                        idx = 1
            if idx != -1:
                self.model.container.selected_item = idx
