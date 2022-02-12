

from quivilib.resources import images

import wx
import sys

ART_THUMBNAIL_VIEW = b'quiviART_THUMBNAIL_VIEW'

raw_IMG_MAP_16 = {
    wx.ART_FOLDER_OPEN: 'folder_yellow_open',
    wx.ART_GO_DIR_UP: 'folder_green_up',
    wx.ART_ADD_BOOKMARK: 'folder_yellow_add_favorite',
    wx.ART_DEL_BOOKMARK: 'folder_yellow_remove_favorite',
    ART_THUMBNAIL_VIEW: 'view_icon',
}

class QuiviArtProvider(wx.ArtProvider):
    def __init__(self, *args, **kwds):
        #the wx.* constants are binary strings, while the incoming artids are unicode strings.
        #Convert the lookup table to use unicode strings, and reference that.
        self._IMG_MAP_16 = {k.decode('ascii'): v for k, v in raw_IMG_MAP_16.items()}
        wx.ArtProvider.__init__(self, *args, **kwds)
    def CreateBitmap(self, artid, client, size):
        bmp = wx.NullBitmap
        if size.width == 16:
            if artid in self._IMG_MAP_16:
                return getattr(images, self._IMG_MAP_16[artid]).Bitmap
        
        return bmp
