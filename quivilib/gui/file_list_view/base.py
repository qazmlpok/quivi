import wx
from pubsub import pub as Publisher
from wx import FileDataObject, DropSource

from quivilib.model.favorites import FavoriteMenuItem


class FileListViewBase(object):
    def __init__(self):
        pass
    
    def on_context_menu(self, event):
        menu = wx.Menu()
        #Kinda ugly reference to the MainWindow list of favorites...
        fav_list: list[FavoriteMenuItem] = self.Parent.Parent.favorites_menu_items
        for item in fav_list:
            menu.Append(item.ide, item.name)
        #The event handlers were already set by the MainWindow.
        self.PopupMenu(menu)
        menu.Destroy()
        
    def on_begin_drag(self, event):
        sel = self._get_selected_index()
        if sel == -1:
            return
        class Dummy:
            idx = sel
            path = None
        obj = Dummy()
        Publisher.sendMessage('file_list.begin_drag', obj=obj)
        if obj.path:
            do = FileDataObject()
            do.AddFile(obj.path)
            ds = DropSource(self)
            ds.SetData(do)
            ds.DoDragDrop(wx.Drag_CopyOnly)
            
    def _get_selected_index(self):
        raise NotImplementedError()
    
    def show(self):
        raise NotImplementedError()
