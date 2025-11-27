import sys
import logging

import wx
import pyfreeimage as fi
from pyfreeimage import Image
from quivilib.i18n import _
from quivilib.interface.imagehandler import ImageHandler
from quivilib.util import add_exception_custom_msg
from quivilib.util import rescale_by_size_factor

from typing import IO

log = logging.getLogger('freeimage')


class FreeImage(ImageHandler):
    def __init__(self, f:IO[bytes]|None=None, path:str|None=None, img=None, delay=False) -> None:
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
                error_msg += f'\n({fi_error_msg})'
            elif str(e):
                error_msg += f'\n({str(e)})'
            add_exception_custom_msg(e, error_msg)
            raise
        
    def delayed_load(self) -> None:
        if not self.delay:
            log.debug("delayed_load was called but delay was off")
            return
        if sys.platform != 'win32':
            self.bmp = self.img.convert_to_wx_bitmap(wx)
            if self.zoomed_bmp:
                self.zoomed_bmp = self.zoomed_bmp.convert_to_wx_bitmap(wx)
        self.delay = False

    def rescale(self, width, height):
        #TODO: Make sure this isn't called multiple times with the same dimensions.
        #I don't want to actually store this in zoomed_bmp, but something similar is fine.
        return self.img.rescale(width, height, fi.FILTER_BICUBIC)

    def resize(self, width: int, height: int) -> None:
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
        
    def resize_by_factor(self, factor: float) -> None:
        width = int(self.original_width * factor)
        height = int(self.original_height * factor)
        self.resize(width, height)
        
    def rotate(self, clockwise: int) -> None:
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
        
    def paint(self, dc, x: int, y: int) -> None:
        if self.delay:
            log.error("paint called but image was not loaded")
            return
        if sys.platform == 'win32':
            import win32gui, win32con
            import ctypes
            gdi32 = ctypes.windll.gdi32
            #hdc = dc.GetHDC()
            #https://discuss.wxpython.org/t/gethandle-example/30032/5 - GetHandle is not a drop-in replacement for GetHDC
            hdc = ctypes.c_ulong(dc.GetHandle()).value
            img = self.zoomed_bmp if self.zoomed_bmp else self.img
            win32gui.SetStretchBltMode(hdc, win32con.COLORONCOLOR)
            gdi32.StretchDIBits(hdc, x, y, img.width, img.height,
                                0, 0, img.width, img.height, img.bits, img.info,
                                win32con.DIB_RGB_COLORS, win32con.SRCCOPY)
        else:
            bmp = self.zoomed_bmp if self.zoomed_bmp else self.bmp
            dc.DrawBitmap(bmp, x, y)
            
    def copy(self) -> ImageHandler:
        return FreeImage(img=self.img)
    
    def copy_to_clipboard(self) -> None:
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

    def create_thumbnail(self, width: int, height: int, delay: bool = False):
        factor = rescale_by_size_factor(self.original_width, self.original_height, width, height)
        factor = min(factor, 1)
        width = int(self.original_width * factor)
        height = int(self.original_height * factor)
        img = self.img.rescale(width, height, fi.FILTER_BILINEAR)
        if delay:
            def delayed_fn(_img=img, _wx=wx):
                return _img.convert_to_wx_bitmap(_wx)
            return delayed_fn
        else:
            bmp = img.convert_to_wx_bitmap(wx)
            return bmp

    @staticmethod
    def _get_extensions():
        return fi.library.load().get_readable_extensions()
    ext_list = _get_extensions()
    
    @staticmethod
    def extensions():
        return FreeImage.ext_list

    def close(self):
        pass
