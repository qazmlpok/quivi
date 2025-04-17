#Debug window. Should only be referenced when running through the command line.

import os
import wx
from pubsub import pub as Publisher

WINDOW_SIZE = (400, 480)

#Meaningful text in the grid. Other items may be used but don't have a special meaning.
QUEUED = 'Queued'
LOADED = 'Loaded'


class DebugDialog(wx.Dialog):
    """Debug window for showing some application information.
    Unlike most windows, this will always exist and is shown/hidden.
    This is because the cache list form listens to events directly.
    Probably a bad idea but this is a debug thing, so I'm not too concerned.
    """
    def __init__(self, parent):
        # begin wxGlade: OptionsDialog.__init__
        wx.Dialog.__init__(self, parent=parent, style=wx.DEFAULT_DIALOG_STYLE|wx.RESIZE_BORDER|wx.DIALOG_NO_PARENT|wx.STAY_ON_TOP)
        
        #Information on loaded/cached images.
        self.cache_list = DebugListCtrl(self)
        #Maybe another control for showing (relevant) messages?
        self.ok_button = wx.Button(self, wx.ID_OK, "&OK")

        self.__set_properties()
        self.__do_layout()
        
        #Do this after do_layout for GetBestSize() to work.
        bestsize = self.GetBestSize()
        self.SetSize(max(bestsize[0], WINDOW_SIZE[0]), max(bestsize[1], WINDOW_SIZE[1]))
        self.Centre()
        
        self.Bind(wx.EVT_BUTTON, self.on_ok_click, self.ok_button)

    def __set_properties(self):
        # begin wxGlade: OptionsDialog.__set_properties
        self.SetTitle("Debug information")
        # end wxGlade
        
        self.ok_button.SetDefault()

    def __do_layout(self):
        # begin wxGlade: OptionsDialog.__do_layout
        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer.Add(self.cache_list, wx.EXPAND)
        sizer.Add(self.ok_button)
        self.SetSizer(sizer)
        
        self.Layout()
        # end wxGlade


    def on_ok_click(self, event): # wxGlade: OptionsDialog.<event_handler>
        #This window needs to always be alive; don't destroy it.
        self.Hide()


# end of class DebugDialog

class DebugListCtrl(wx.ListCtrl):
    """ List view of the images known to the cache. Listens to the same events the cache does, plus
    events emitted by the cache. Uses this to roughly duplicate the cache behavior.
    It's not exact - items dropped from the cache are kept in the list but marked as removed.
    This also means it won't actually show what's _really_ happening with the cache, which is unfortunate.
    """
    column_order = ['id', 'filename', 'queue', 'cache', 'resolution']
    column_headers = ['', 'File', 'Queue', 'Cache', 'Resolution']
    def __init__(self, parent):
        wx.ListCtrl.__init__(
            self, parent, -1, 
            style=wx.LC_REPORT|wx.LC_SINGLE_SEL
            )
        for i in range(len(DebugListCtrl.column_headers)):
            self.InsertColumn(i, DebugListCtrl.column_headers[i])
        self.SetColumnWidth(0, 25)
        self.SetColumnWidth(1, 240)
        self.SetColumnWidth(2, 80)
        self.SetColumnWidth(3, 80)
        self.SetColumnWidth(4, 200)
        
        #Dictionary of the Cache and Queue data. Updated based on messages;
        #either the same ones that the Cache worker responds to, or the outgoing messages
        #(Including at least one debug message that is only sent for this control)
        #Key will be the full path.
        self.cache_data = {}
        #Alternative lookup table. Needed for sorting.
        self.cache_data_id = {}
        #Needed to get the original row after sorting...
        self.sorted_indices = {}
        
        #Messages the cache listens for
        Publisher.subscribe(self.on_load_image, 'cache.load_image')
        Publisher.subscribe(self.on_clear_pending, 'cache.clear_pending')
        Publisher.subscribe(self.on_flush, 'cache.flush')
        #Publisher.subscribe(self.on_program_closed, 'program.closed')  #This really doesn't matter.
        
        #Messages sent by the cache
        Publisher.subscribe(self.on_cache_image_loaded, 'cache.image_loaded')
        Publisher.subscribe(self.on_cache_image_load_error, 'cache.image_load_error')
        Publisher.subscribe(self.on_cache_image_removed, 'cache.image_removed')
    #
    def create_entry(self, request):
        return {
            'id': 0,
            'path': request.path,
            'filename': os.path.basename(request.path),
            'queue': QUEUED,
            'cache': '',
            'resolution': '',
        }
    def get_or_insert(self, request):
        path = request.path
        if path in self.cache_data:
            return self.cache_data[path]
        entry = self.create_entry(request)
        self.add_list_item(entry)
        #Local lookup tables. I don't think the base listctrl exposes any real "find" methods.
        self.cache_data[path] = entry
        self.cache_data_id[entry['id']] = entry
        self.update_list_item(entry)
        return entry
    def add_list_item(self, entry):
        """ Add an entry to the actual list control.
        Modifies the entry object to include the id; use this for future requests
        """
        #I want this to display the numeric index of the list; I guess this is just how to do it.
        index = self.InsertItem(self.GetItemCount(), str(self.GetItemCount()))
        self.SetItemData(index, index)  #Must be an int.
        entry['id'] = index
    def update_list_item(self, entry):
        """ Update the list control with the new values.
        """
        #entry['id'] is the unsorted row number. Sorting will change this.
        index = entry['id']
        if index in self.sorted_indices:
            index = self.sorted_indices[index]
        for i in range(len(DebugListCtrl.column_order)):
            key = DebugListCtrl.column_order[i]
            self.SetItem(index, i, str(entry[key]))
        #Note - This modifies the actual index, not just the display order.
        self.SortItems(self.sort_fn)
        self.recalculate_ids()
    def sort_fn(self, id1, id2):
        """ Special sort order - put loaded images first.
        Not using the built-in mixin because I think that's primarily for "direct" sorting.
        """
        item1 = self.cache_data_id[id1]
        item2 = self.cache_data_id[id2]
        k1 = self.sort_key(item1)
        k2 = self.sort_key(item2)
        if (k1 != k2):
            return k2 - k1
        #Equal priority; sort by id
        return item2['id'] - item1['id']
    def sort_key(self, item):
        """ Helper function for sorting; convert text strings to priorities.
        If priorities match, sort_fn will use id. Otherwise higher-priority items are always first.
        """
        if item['queue'] is QUEUED:
            return 1100
        if item['cache'] is LOADED:
            return 1000
        if item['cache'] != '':
            return 110
        if item['queue'] != '':
            return 100
        return 0
    def recalculate_ids(self):
        """ Be sure to call this whenever the rows are sorted.
        Sorting changes the indices. Fetch all of the new data to get the original id (first column)
        I can't find any way to do this automatically.
        """
        self.sorted_indices.clear()
        for i in range(len(self.cache_data_id)):
            txt = self.GetItemText(i, 0)
            self.sorted_indices[int(txt)] = i
    #Events
    def on_load_image(self, *, request, preload=False):
        """ Cache uses this to add an entry to the Queue.
        It will load the image and add it to the cache, then send cache.image_loaded
        """
        entry = self.get_or_insert(request)
        entry['queue'] = QUEUED
        self.update_list_item(entry)
        pass
    def on_clear_pending(self, *, request=None):
        #I think this means any queued-but-not-cached items are dropped.
        for x in self.cache_data:
            entry = self.cache_data[x]
            if entry['queue'] == QUEUED:
                entry['queue'] = 'Abandoned'
                self.update_list_item(entry)
        pass
    def on_flush(self):
        print("on_flush called.")
        #Presumably a new container was loaded, so all old cache entries are meaningless.
        #self.cache_data.clear()
        #self.cache_data_id.clear()
        #self.cache_keys.clear()
        #TODO: Update list items.
        pass
    def on_cache_image_loaded(self, *, request):
        """Sent by the cache when an image is loaded.
        """
        entry = self.get_or_insert(request)
        entry['queue'] = ''
        entry['cache'] = LOADED
        self.update_list_item(entry)
    def on_cache_image_load_error(self, *, request, exception, tb):
        entry = self.get_or_insert(request)
        entry['queue'] = ''
        entry['cache'] = 'Failed'
        self.update_list_item(entry)
    def on_cache_image_removed(self, *, request):
        entry = self.get_or_insert(request)
        entry['cache'] = 'Removed'
        self.update_list_item(entry)

if __name__ == '__main__':
    app = wx.App(False)
    dlg = DebugDialog(None)
    dlg.ShowModal()
