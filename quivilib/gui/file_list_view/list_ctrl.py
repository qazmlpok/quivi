import sys
import wx
from pubsub import pub as Publisher

from quivilib.gui.file_list_view.base import FileListViewBase
from quivilib.i18n import _
from quivilib.util import error_handler
from quivilib.model.container import SortOrder
from quivilib.util import get_icon_for_extension, get_icon_for_directory

def _handle_error(exception, args, kwargs):
    self = args[0]
    self.handle_error(exception)


class FileList(wx.ListCtrl, FileListViewBase):
    def __init__(self, parent):
        wx.ListCtrl.__init__(
            self, parent, -1, 
            style=wx.LC_REPORT|wx.LC_VIRTUAL|wx.LC_SINGLE_SEL 
            )
        
        self.container = None
        self._selecting_programatically = False
        self.image_list = None
        self.flush_icon_cache()

        self.InsertColumn(0, '')
        self.InsertColumn(1, '')
        self.InsertColumn(2, '')
        self.SetColumnWidth(0, 175)
        self.SetColumnWidth(1, 80)
        self.SetColumnWidth(2, 120)
        
        #The name column actually sorts by type
        self.columns = (SortOrder.TYPE, SortOrder.EXTENSION, SortOrder.LAST_MODIFIED)

        self.SetItemCount(0)

        self.Bind(wx.EVT_SIZE, self.on_resize)
        self.Bind(wx.EVT_CONTEXT_MENU, self.on_context_menu)
        self.Bind(wx.EVT_LIST_ITEM_SELECTED, self.on_item_selected)
        self.Bind(wx.EVT_LIST_ITEM_ACTIVATED, self.on_item_activated)
        self.Bind(wx.EVT_LIST_KEY_DOWN, self.on_key_down)
        self.Bind(wx.EVT_LIST_COL_CLICK, self.on_column_click)
        self.Bind(wx.EVT_LIST_COL_END_DRAG, self.on_end_column_drag)
        self.Bind(wx.EVT_LIST_BEGIN_DRAG, self.on_begin_drag)
        Publisher.subscribe(self.on_container_changed, 'container.changed')
        Publisher.subscribe(self.on_selection_changed, 'container.selection_changed')
        Publisher.subscribe(self.on_language_changed, 'language.changed')
        
    @error_handler(_handle_error)
    def on_item_selected(self, event):
        if not self._selecting_programatically:
            Publisher.sendMessage('file_list.selected', index=event.GetIndex())

    @error_handler(_handle_error)
    def on_item_activated(self, event):
        Publisher.sendMessage('file_list.activated', index=event.GetIndex())
        
    def on_key_down(self, event):
        event.Skip()

    def getColumnText(self, index, col):
        item = self.GetItem(index, col)
        return item.GetText()

    def OnGetItemText(self, item, col):
        if col == 0:
            return self.container.get_item_name(item)
        elif col == 1:
            return self.container.get_item_extension(item)
        elif col == 2:
            date = self.container.get_item_last_modified(item)
            if date:
                return date.strftime('%c')
            else:
                return ''
        assert False

    def OnGetItemImage(self, item):
        ext = self.container.get_item_extension(item)
        if ext in self.icon_cache:
            icon_index = self.icon_cache[ext]
        else:
            #TODO: (3,3) Improve: on windows, get custom icon for folders, ico files, drives
            icon = None
            if ext:
                #TODO: (1,3) Improve: check item type instead of ext?
                icon = get_icon_for_extension('.' + ext)
            else:
                #TODO: *(1,1) Improve: cache directory icon
                icon = get_icon_for_directory()
            if icon:
                icon_index = self.image_list.Add(icon)
            else:
                icon_index = None
            self.icon_cache[ext] = icon_index
        return icon_index

    def OnGetItemAttr(self, item):
        return None
    
    def on_container_changed(self, *, container):
        self.container = container
        old_sel = self.GetFirstSelected()
        self.flush_icon_cache()
        if sys.platform != 'win32' and old_sel != -1:
            #On Linux the selected/focused item keeps its state even after
            #resetting the item count. On Windows this causes GetItemText being
            #called with an index possibly bigger than the item count
            self.SetItemState(0, 0, wx.LIST_STATE_SELECTED | wx.LIST_STATE_FOCUSED)
        #This is required to clear any previous selection
        sel = self.container.selected_item_index
        self.SetItemCount(0)
        self.SetItemCount(len(self.container.items))
        self.Refresh()
        if sel >= 0:
            self.on_selection_changed(idx=sel, item=self.container.selected_item)
        
    def flush_icon_cache(self):
        self.icon_cache = {}
        #TODO: (1,3) Improve: get size from somewhere
        self.image_list = wx.ImageList(16, 16)
        self.SetImageList(self.image_list, wx.IMAGE_LIST_SMALL)
        
    def on_selection_changed(self, *, idx, item):
        self._selecting_programatically = True
        try:
            self.SetItemState(idx, wx.LIST_STATE_SELECTED | wx.LIST_STATE_FOCUSED,
                              wx.LIST_STATE_SELECTED | wx.LIST_STATE_FOCUSED)
            self.EnsureVisible(idx)
        finally:
            self._selecting_programatically = False
            
    def on_language_changed(self):
        def set_col_text(col, text):
            item = wx.ListItem()
            item.Text = text
            item.Mask = wx.LIST_MASK_TEXT
            self.SetColumn(col, item)
        
        set_col_text(0, _('File'))
        set_col_text(1, _('Extension'))
        set_col_text(2, _('Last modified'))
            
    def on_column_click(self, event):
        col = event.GetColumn()
        sort_order = self.columns[col]
        Publisher.sendMessage('file_list.column_clicked', sort_order=sort_order)
            
    def on_resize(self, event):
        #TODO: (4,?) Investigate: uncommenting this line causes a bizarre bug
        #    in the GUI when opening a container
        #    (the file list gets a huge padding above the content)
        #self._adjust_columns()
        event.Skip()
     
    def on_end_column_drag(self, event):
        pass
        #self._adjust_columns()
        #event.Veto()
        
    def _adjust_columns(self):
        #TODO: (1,?) Fix: When making window smaller, a horizontal scroll
        #    appears sometimes. It shouldn't.
        width = self.GetClientSize()[0]
        used_width = sum(self.GetColumnWidth(i) for i
                         in range(1, self.GetColumnCount()))
        self.SetColumnWidth(0, width - used_width - 5)
        
    def save(self, settings_lst):
        widths = ','.join(str(self.GetColumnWidth(i))
                          for i in range(self.GetColumnCount()))
        settings_lst.append(('Window', 'FileListColumnsWidth', widths))
    
    def load(self, settings):
        widths = settings.get('Window', 'FileListColumnsWidth')
        if widths:
            for i, width_str in enumerate(widths.split(',')):
                if i < self.GetColumnCount():
                    try:
                        self.SetColumnWidth(i, int(width_str))
                    except ValueError:
                        #TODO: (1,3) Improve: log
                        pass
                    
    def handle_error(self, exception):
        self.Parent.Parent.handle_error(exception)
        
    def _get_selected_index(self):
        return self.GetFirstSelected()

    def show(self):
        pass
