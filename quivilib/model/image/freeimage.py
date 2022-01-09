

from quivilib.i18n import _
from quivilib.util import add_exception_custom_msg
from quivilib.util import rescale_by_size_factor

import pyfreeimage as fi
from pyfreeimage import Image

import wx

import sys
import logging

log = logging.getLogger('freeimage')



class FreeImage(object):
    def __init__(self, canvas_type, f=None, path=None, img=None, delay=False):
        self.canvas_type = canvas_type
        self.delay = delay
        
        try:
            if img is None:
                fi.library.load().reset_last_error()
                img = Image.load_from_file(f, path)
                try:
                    if img.transparent:
                        img = img.composite(True)
                except RuntimeError:
                    pass
                if sys.platform == 'win32':
                    if img.bpp != 24:
                        img = img.convert_to_24_bits()
                else:
                    img = img.convert_to_32_bits()
            
            if sys.platform != 'win32':
                if self.delay:
                    self.bmp = None
                else:
                    self.bmp = img.convert_to_wx_bitmap(wx)
            
            self.original_width = self.width = img.width
            self.original_height = self.height = img.height
            
            self.img = img
            self.zoomed_bmp = None 
            self.rotation = 0
        except Exception as e:
            error_msg = _('Error while loading image')
            fi_error_msg = fi.library.load().last_error
            if fi_error_msg:
                error_msg += '\n(%s)' % fi_error_msg
            elif str(e):
                error_msg += '\n(%s)' % str(e)
            add_exception_custom_msg(e, error_msg)
            raise
        
    def delayed_load(self):
        if not self.delay:
            log.debug("delayed_load was called but delay was off")
            return
        if sys.platform != 'win32':
            self.bmp = self.img.convert_to_wx_bitmap(wx)
            if self.zoomed_bmp:
                self.zoomed_bmp = self.zoomed_bmp.convert_to_wx_bitmap(wx)
        self.delay = False
        
    def resize(self, width, height):
        if self.original_width == width and self.original_height == height:
            self.zoomed_bmp = None
        else:
            img = self.img.rescale(width, height, fi.FILTER_BICUBIC)
            if sys.platform != 'win32':
                if self.delay:
                    self.zoomed_bmp = img
                else:
                    self.zoomed_bmp = img.convert_to_wx_bitmap(wx)
            else:
                self.zoomed_bmp = img
        self.width = width
        self.height = height
        
    def resize_by_factor(self, factor):
        width = int(self.original_width * factor)
        height = int(self.original_height * factor)
        self.resize(width, height)
        
    def rotate(self, clockwise):
        self.rotation += (1 if clockwise else -1)
        self.rotation %= 4
        self.img = self.img.rotate(90 if clockwise else 270)
        self.original_width = self.img.width
        self.original_height = self.img.height
        if self.zoomed_bmp:
            if self.rotation in (1, 3):
                w, h = self.height, self.width
            else:
                w, h = self.width, self.height
            self.resize(w, h)
        else:
            self.width = self.original_width
            self.height = self.original_height
        
    def paint(self, dc, x, y):
        if self.delay:
            log.error("paint called but image was not loaded")
            return
        if sys.platform == 'win32':
            import win32gui, win32con
            import ctypes
            gdi32 = ctypes.windll.gdi32
            hdc = dc.GetHDC()
            img = self.zoomed_bmp if self.zoomed_bmp else self.img
            win32gui.SetStretchBltMode(hdc, win32con.COLORONCOLOR)
            gdi32.StretchDIBits(hdc, x, y, img.width, img.height,
                                0, 0, img.width, img.height, img.bits, img.info,
                                win32con.DIB_RGB_COLORS, win32con.SRCCOPY)
        else:
            bmp = self.zoomed_bmp if self.zoomed_bmp else self.bmp
            dc.DrawBitmap(bmp, x, y)
            
    def copy(self):
        return FreeImage(self.canvas_type, img=self.img)
    
    def copy_to_clipboard(self):
        if sys.platform == 'win32':
            #TODO: (2,2) Improve: there's a better way to do this with Win32 API
            #    (check FreeImagePlus's copy)
            bmp = self.img.convert_to_wx_bitmap(wx)
            data = wx.BitmapDataObject(bmp)
            if wx.TheClipboard.Open():
                wx.TheClipboard.SetData(data)
                wx.TheClipboard.Close()
        else:
            data = wx.BitmapDataObject(self.bmp)
            if wx.TheClipboard.Open():
                wx.TheClipboard.SetData(data)
                wx.TheClipboard.Close()
                
    def create_thumbnail(self, width, height, delay=False):
        factor = rescale_by_size_factor(self.original_width, self.original_height, width, height)
        if factor > 1:
            factor = 1
        width = int(self.original_width * factor)
        height = int(self.original_height * factor)
        img = self.img.rescale(width, height, fi.FILTER_BILINEAR)
        if delay:
            def delayed_fn(img=img, wx=wx):
                return img.convert_to_wx_bitmap(wx)
            return delayed_fn
        else:
            bmp = img.convert_to_wx_bitmap(wx)
            return bmp
                
    def close(self):
        pass
