

from quivilib.resources import images

import wx
import sys

ART_THUMBNAIL_VIEW = 'quiviART_THUMBNAIL_VIEW'

_IMG_MAP_16 = {
    wx.ART_FOLDER_OPEN: 'folder_yellow_open',
    wx.ART_GO_DIR_UP: 'folder_green_up',
    wx.ART_ADD_BOOKMARK: 'folder_yellow_add_favorite',
    wx.ART_DEL_BOOKMARK: 'folder_yellow_remove_favorite',
    ART_THUMBNAIL_VIEW: 'view_icon',
}



class QuiviArtProvider(wx.ArtProvider):
    def CreateBitmap(self, artid, client, size):
        bmp = wx.NullBitmap
        if size.width == 16:
            if artid in _IMG_MAP_16:
                return getattr(images, _IMG_MAP_16[artid]).Bitmap
        
        return bmp
    