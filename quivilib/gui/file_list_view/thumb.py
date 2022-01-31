from quivilib.model import image
from quivilib.model.container import Item
from quivilib import util
from quivilib.util import error_handler
from quivilib.gui.file_list_view.base import FileListViewBase
from wx.lib.agw import thumbnailctrl as tc
import wx.lib.agw.scrolledthumbnail as st
from wx.lib.agw.thumbnailctrl import (
    THUMB_OUTLINE_FULL, THUMB_OUTLINE_IMAGE, THUMB_OUTLINE_NONE,
    THUMB_OUTLINE_RECT)

import wx
from pubsub import pub as Publisher

import threading
import math
import logging
import collections
log = logging.getLogger('thumb')

OldScrolledThumbnail = None


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
    def BreakCaption(self, width):
        """ Breaks the caption in several lines of text (if needed). """
        self._captionbreaks = [0, None]
        return
        
        self._captionbreaks = []
        self._captionbreaks.append(0)
        if len(self._caption) == 0:
            return
        pos = width/16
        beg = 0
        dc = wx.MemoryDC()
        bmp = wx.EmptyBitmap(10,10)
        dc.SelectObject(bmp)
        dc.SetFont(self._parent.GetCaptionFont())
        
        while True:
            if pos >= len(self._caption):
                self._captionbreaks.append(len(self._caption))
                break
            line = self._caption[beg:pos]
            sw = dc.GetTextExtent(line)[0]
            if  sw > width:
                self._captionbreaks.append(pos)
                beg = pos
                pos = beg + width/16
            pos += 1

        dc.SelectObject(wx.NullBitmap)

    def GetBitmap(self, width, height):
        """ Returns the associated bitmap. """

        if self._bitmap:
            if isinstance(self._bitmap, collections.Callable):
                self._bitmap = self._bitmap()
            if self._bitmap.GetWidth() == width and self._bitmap.GetHeight() == height:
                return self._bitmap

        img = self.GetThumbnail(width, height)
        bmp = img.ConvertToBitmap()

        return bmp

class QuiviScrolledThumbnail(tc.ScrolledThumbnail):
    def __init__(self, *args, **kwargs):
        OldScrolledThumbnail.__init__(self, *args, **kwargs)
        self._tOutlineNotSelected = False
        self._thread = None
        Publisher.subscribe(self.on_program_closed, 'program.closed')
        
    def on_program_closed(self, *, settings_lst=None):
        self._isrunning = False
        if self._thread:
            self._thread.join()
        
    def ThreadImageContainer(self, container):
        """ Threaded method to load images. Used internally. """
        
        for count, item in enumerate(container.items):
            log.debug('Loading thumb #%d' % count)
            if not self._isrunning:
                return
            try:
                self.LoadImageContainer(container, item, count)
            except:
                log.debug("Failed to generate thumbnail for image #%d" % count, exc_info=1)
            log.debug('Loaded thumb #%d' % count)
            if count < 4:
                wx.CallAfter(self.Refresh)
            elif count%4 == 0:
                wx.CallAfter(self.Refresh)
            log.debug('Refresh requested')

        wx.CallAfter(self.Refresh)
        log.debug('Thumbs done!')
        self._isrunning = False

    def LoadImageContainer(self, container, item, index):
        """ Threaded method to load images. Used internally. """
        #TODO: (2,2) Refactor: this should be moved inside the Item class
        bmp = None
        if item.typ == Item.IMAGE:
            f = container.open_image(index)
            try:
                img = image.open(f, item.path, None)
            finally:
                f.close()
            originalsize = (img.original_width, img.original_height)
            bmp = img.create_thumbnail(300, 240, delay=True)
            alpha = False
            def delayed_fn(bmp=bmp):
                if isinstance(bmp, collections.Callable):
                    bmp = bmp()
                img = bmp.ConvertToImage()
                return img
        elif item.typ in (Item.DIRECTORY, Item.PARENT):
            originalsize = 32, 32
            alpha = True
            def delayed_fn(bmp=bmp):
                icon = util.get_icon_for_directory(small=False)
                bmp = wx.Bitmap(icon.GetWidth(), icon.GetHeight())
                bmp.CopyFromIcon(icon)
                img = bmp.ConvertToImage()
                return img
        elif item.typ == Item.COMPRESSED:
            originalsize = 32, 32
            alpha = True
            ext = container.get_item_extension(index)
            def delayed_fn(bmp=bmp, ext=ext):
                icon = util.get_icon_for_extension('.' + ext, small=False)
                bmp = wx.Bitmap(icon.GetWidth(), icon.GetHeight())
                bmp.CopyFromIcon(icon)
                img = bmp.ConvertToImage()
                return img

        self._items[index]._originalsize = originalsize
        self._items[index]._bitmap = delayed_fn
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
        
    #The changes made here appear to be mostly styling
    #def DrawThumbnail(self, bmp, thumb, index):
    #    """ Draws the visible thumbnails. """
    #
    #    dc = wx.MemoryDC()
    #    dc.SelectObject(bmp)
    #    dc.BeginDrawing()
    #    
    #    x = self._tBorder/2
    #    y = self._tBorder/2
    #
    #    # background
    #    dc.SetPen(wx.Pen(wx.BLACK, 0, wx.TRANSPARENT))
    #    dc.SetBrush(wx.Brush(self.GetBackgroundColour(), wx.SOLID))
    #    dc.DrawRectangle(0, 0, bmp.GetWidth(), bmp.GetHeight())
    #    
    #    # image
    #    img = thumb.GetBitmap(self._tWidth, self._tHeight)
    #    ww = img.GetWidth()
    #    hh = img.GetHeight()
    #    
    #    imgRect = wx.Rect(x + (self._tWidth - img.GetWidth())/2,
    #                      y + (self._tHeight - img.GetHeight())/2,
    #                      img.GetWidth(), img.GetHeight())
    #
#   #     if not thumb._alpha:
#   #         dc.Blit(imgRect.x+5, imgRect.y+5, imgRect.width, imgRect.height, self.shadow, 500-ww, 500-hh)        
    #    dc.DrawBitmap(img, imgRect.x, imgRect.y, True)
    #
    #    colour = self.GetSelectionColour()
    #    selected = self.IsSelected(index)
    #
    #    # draw caption
    #    sw, sh = 0, 0
    #    if self._showfilenames:
    #        textWidth = 0
    #        dc.SetFont(self.GetCaptionFont())
    #        mycaption = thumb.GetCaption(0)
    #        sw, sh = dc.GetTextExtent(mycaption)
    #
    #        if sw > self._tWidth:
    #            mycaption = self.CalculateBestCaption(dc, mycaption, sw, self._tWidth)
    #            sw = self._tWidth
    #        
    #        if selected:
    #            dc.SetTextForeground(wx.SystemSettings.GetColour(wx.SYS_COLOUR_HIGHLIGHTTEXT))
    #            dc.SetTextBackground(wx.SystemSettings.GetColour(wx.SYS_COLOUR_HIGHLIGHT))
    #            dc.SetBrush(wx.Brush(wx.SystemSettings.GetColour(wx.SYS_COLOUR_HIGHLIGHT)))
    #        
    #        tx = x + (self._tWidth - sw)/2
    #        ty = y + self._tHeight + (self._tTextHeight - sh)/2 + 3
    #
    #        lines = thumb.GetCaptionLinesCount(self._tWidth)
    #        if selected:
    #            dc.DrawRectangle(tx-2, ty-2, sw+4, (sh*lines)+4)
    #        
    #        if lines == 1:
    #            dc.DrawText(mycaption, tx, ty)
    #        else:
    #            start = 0
    #            for end in thumb._captionbreaks[1:]:
    #                dc.DrawText(thumb._caption[start:end], x, ty)
    #                start = end
    #                ty += sh
    #        
    #    # outline
    #    if self._tOutline != tc.THUMB_OUTLINE_NONE and (self._tOutlineNotSelected or selected):
    #
    #        dotrect = wx.Rect()
    #        dotrect.x = x - 2
    #        dotrect.y = y - 2
    #        dotrect.width = bmp.GetWidth() - self._tBorder + 4
    #        dotrect.height = bmp.GetHeight() - self._tBorder + 4
    #    
    #        dc.SetPen(wx.Pen((self.IsSelected(index) and [colour] or [wx.LIGHT_GREY])[0],
    #                         0, wx.SOLID))       
    #        dc.SetBrush(wx.Brush(wx.BLACK, wx.TRANSPARENT))
    #    
    #        if self._tOutline == tc.THUMB_OUTLINE_FULL or self._tOutline == tc.THUMB_OUTLINE_RECT:
    #
    #            imgRect.x = x
    #            imgRect.y = y
    #            imgRect.width = bmp.GetWidth() - self._tBorder
    #            imgRect.height = bmp.GetHeight() - self._tBorder
    #
    #            if self._tOutline == tc.THUMB_OUTLINE_RECT:
    #                imgRect.height = self._tHeight             
    #
    #        dc.SetBrush(wx.TRANSPARENT_BRUSH)
    #
    #        if selected:
    #
#   #             dc.SetPen(self.grayPen)
#   #             dc.DrawRoundedRectangleRect(dotrect, 2)
    #            
#   #             dc.SetPen(wx.Pen(wx.WHITE))
#   #             dc.DrawRectangle(imgRect.x, imgRect.y,
#   #                              imgRect.width, imgRect.height)
    #
    #            pen = wx.Pen((selected and [colour] or [wx.LIGHT_GREY])[0], 2)
    #            pen.SetJoin(wx.JOIN_MITER)
    #            dc.SetPen(pen)
    #            if self._tOutline == tc.THUMB_OUTLINE_FULL:
    #                dc.DrawRoundedRectangle(imgRect.x - 1, imgRect.y - 1,
    #                                        imgRect.width + 3, imgRect.height + 3, 2)
    #            else:
    #                dc.DrawRectangle(imgRect.x, imgRect.y,
    #                                 imgRect.width, imgRect.height)
    #        else:
    #            dc.SetPen(wx.Pen(wx.LIGHT_GREY))
    #
    #            dc.DrawRectangle(imgRect.x - 1, imgRect.y - 1,
    #                             imgRect.width + 2, imgRect.height + 2)
    #        
    #
    #    dc.EndDrawing()
    #    dc.SelectObject(wx.NullBitmap)

    def DeleteFiles(self):
        pass
