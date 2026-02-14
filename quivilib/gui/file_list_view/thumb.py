import logging
import threading

from pubsub import pub as Publisher
import wx
from wx.lib.agw import thumbnailctrl as tc
import wx.lib.agw.scrolledthumbnail as st
from wx.lib.agw.thumbnailctrl import (
    THUMB_OUTLINE_FULL, THUMB_OUTLINE_IMAGE, THUMB_OUTLINE_NONE,
    THUMB_OUTLINE_RECT)

from quivilib.model import image
from quivilib.model.container import Item, ItemType
from quivilib import util
from quivilib.util import error_handler, DebugTimer
from quivilib.gui.file_list_view.base import FileListViewBase

log = logging.getLogger('thumb')

OldScrolledThumbnail = None

if __debug__:
    import time

def _handle_error(exception, args, kwargs):
    self = args[0]
    self.handle_error(exception)


class QuiviThumbnailCtrl(tc.ThumbnailCtrl, FileListViewBase):
    def __init__(self, *args, **kwargs):
        #Here we patch the default ScrolledThumbnail with ours
        global OldScrolledThumbnail, OldThumb
        OldScrolledThumbnail = tc.ScrolledThumbnail
        tc.ScrolledThumbnail = QuiviScrolledThumbnail
        tc.ThumbnailCtrl.__init__(self, *args, **kwargs)
        tc.ScrolledThumbnail = OldScrolledThumbnail
        #
        self.container = None
        self._selecting_programatically = False
        self._delayed_load = False
        
        self.Bind(wx.EVT_CONTEXT_MENU, self.on_context_menu)
        self.Bind(st.EVT_THUMBNAILS_SEL_CHANGED, self.on_item_selected)
        self.Bind(wx.EVT_LIST_ITEM_SELECTED, self.on_item_selected)
        self.Bind(st.EVT_THUMBNAILS_DCLICK, self.on_item_activated)
        Publisher.subscribe(self.on_container_changed, 'container.changed')
        Publisher.subscribe(self.on_selection_changed, 'container.selection_changed')
        
    @error_handler(_handle_error)
    def on_item_selected(self, event):
        if not self._selecting_programatically:
            Publisher.sendMessage('file_list.selected', index=self.GetSelection())
            
    @error_handler(_handle_error)
    def on_item_activated(self, event):
        Publisher.sendMessage('file_list.activated', index=self.GetSelection())
    def on_container_changed(self, *, container):
        self.container = container
        sel = self.container.selected_item_index
        self._delayed_load = not self.Parent.is_thumbnails()
        if not self._delayed_load:
            self._scrolled.ShowContainer(self.container, True)
            if sel >= 0:
                self.on_selection_changed(idx=sel, item=self.container.selected_item)
        
    def on_selection_changed(self, *, idx, item):
        if not self._delayed_load:
            self._selecting_programatically = True
            try:
                if idx < self.GetItemCount():
                    self.SetSelection(idx)
            finally:
                self._selecting_programatically = False
            
    def _get_selected_index(self):
        return self.GetSelection()
    
    def show(self):
        if self._delayed_load:
            self._scrolled.ShowContainer(self.container, True)
            self._delayed_load = False

class QuiviThumb(tc.Thumb):
    def __init__(self, *args, **kwargs):
        tc.Thumb.__init__(self, *args, **kwargs)
        self.delay_fn = None
    def DelayLoad(self):
        """ Executes the delay load function and populates _image with the result.
        This needs to be called before any references to _image in the base class.
        """
        if self.delay_fn:
            self._image = self.delay_fn()
            self._bitmap = None     #Bitmap should be re-created.
            #I think if this is an icon (which is made to size) bmp can be re-used from the img generation.
            #Try that later.
            self.delay_fn = None
    def BreakCaption(self, width):
        """ Breaks the caption in several lines of text (if needed). """
        self._captionbreaks = [0, None]
        return

    def GetBitmap(self, width, height):
        self.DelayLoad()
        return super().GetBitmap(width, height)
    def GetImage(self):
        self.DelayLoad()
        return super().GetImage()
    def GetThumbnail(self, width, height):
        self.DelayLoad()
        return super().GetThumbnail(width, height)
    def Rotate(self, angle):
        self.DelayLoad()
        return super().Rotate(angle)
    #SetImage? LoadImage? (clear delay fn)

class QuiviScrolledThumbnail(tc.ScrolledThumbnail):
    def __init__(self, *args, **kwargs):
        OldScrolledThumbnail.__init__(self, *args, **kwargs)
        self._tOutlineNotSelected = False
        self.thumbs_generated = False
        self._isrunning = False
        self._thread = None
        Publisher.subscribe(self.on_program_closed, 'program.closed')
        self.SetDropShadow(False)

    def ShowThumbs(self, thumbs):
        #Prevent default behavior. GenerateThumbs handles the thread
        pass
        
    def on_program_closed(self, *, settings_lst=None):
        self._isrunning = False
        if self._thread:
            self._thread.join()
        
    def ThreadImageContainer(self, container):
        """ Threaded method to load images. Used internally. """
        
        for count, item in enumerate(container.items):
            with DebugTimer(f'Loaded thumb #{count}.'):
                if not self._isrunning:
                    return
                try:
                    self.LoadImageContainer(container, item, count)
                except:
                    log.debug("Failed to generate thumbnail for image #%d" % count, exc_info=True)
            if count < 4 or count%4 == 0:
                wx.CallAfter(self.Refresh)
                log.debug('Refresh requested')

        wx.CallAfter(self.Refresh)
        log.debug('Thumbs done!')
        self._isrunning = False

    def LoadImageContainer(self, container, item, index) -> None:
        """ Threaded method to load images. Used internally. """
        #TODO: (2,2) Refactor: this should be moved inside the Item class
        bmp = None
        if item.typ == ItemType.IMAGE:
            f = container.open_image(index)
            try:
                img = image.open(f, item.path)
            finally:
                f.close()
            originalsize = (img.base_width, img.base_height)
            bmp = img.create_thumbnail(300, 240, delay=True)
            alpha = False
            def delayed_fn(_bmp=bmp, _ext=None):
                if callable(_bmp):
                    _bmp = _bmp()
                _img = _bmp.ConvertToImage()
                return _img
        elif item.typ in (ItemType.DIRECTORY, ItemType.PARENT):
            originalsize = 32, 32
            alpha = True
            def delayed_fn(_bmp=bmp, _ext=None):
                icon = util.get_icon_for_directory(small=False)
                _bmp = wx.Bitmap(icon.GetWidth(), icon.GetHeight())
                _bmp.CopyFromIcon(icon)
                _img = _bmp.ConvertToImage()
                return _img
        elif item.typ == ItemType.COMPRESSED:
            originalsize = 32, 32
            alpha = True
            ext = container.get_item_extension(index)
            def delayed_fn(_bmp=bmp, _ext=ext):
                icon = util.get_icon_for_extension('.' + _ext, small=False)
                _bmp = wx.Bitmap(icon.GetWidth(), icon.GetHeight())
                _bmp.CopyFromIcon(icon)
                _img = _bmp.ConvertToImage()
                return _img

        self._items[index]._originalsize = originalsize
        self._items[index].delay_fn = delayed_fn
        self._items[index]._alpha = alpha

    def ShowContainer(self, container, create_thumbs):
        #self.SetCaption('')
        
        self._isrunning = False
        if self._thread:
            self._thread.join()

        # update items
        self._items = []

        for item in container.items:
            caption = item.name if self._showfilenames else ''
            lastmod = item.last_modified
            
            #TODO: Use st.NativeImageHandler if PIL isn't available
            self._items.append(QuiviThumb(item.path.parent, item.path.name, 
                    caption=caption, size=0, lastmod=lastmod, 
                    imagehandler=st.PILImageHandler)
            )

        self.thumbs_generated = False
        if create_thumbs:
            self.GenerateThumbs(container)
            
        self._selectedarray = []
        self.UpdateProp()
        self.Refresh()
        self.UpdateShow()

    def GenerateThumbs(self, container):
        if not self.thumbs_generated:
            self._isrunning = True
            self._thread = threading.Thread(target=self.ThreadImageContainer, args=(container,))
            self._thread.start()
        self.thumbs_generated = True
        
    #The default control truncates from the left. Unchanged since v2
    def CalculateBestCaption(self, dc, caption, sw, width):
        """ Calculate the best caption based on the actual zoom. """

        caption = caption + "..."
        
        while sw > width:
            caption = caption[0:-1]
            sw, sh = dc.GetTextExtent(caption)
            
        return caption[0:-3] + "..."

    def DeleteFiles(self):
        pass
