import sys
import logging
from collections.abc import Callable

import wx
import pyfreeimage as fi
from pyfreeimage import Image
from quivilib.i18n import _
from quivilib.interface.imagehandler import ImageHandlerBase
from quivilib.util import add_exception_custom_msg

from typing import IO, Any, Self

log = logging.getLogger('freeimage')


class FreeImage(ImageHandlerBase):
    @classmethod
    def CreateImage(cls, f:IO[bytes], path:str, delay=False) -> Self:
        try:
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
            return FreeImage(img, path, delay=delay)
        except Exception as e:
            error_msg = _('Error while loading image')
            fi_error_msg = fi.library.load().last_error
            if fi_error_msg:
                error_msg += f'\n({fi_error_msg})'
            elif str(e):
                error_msg += f'\n({str(e)})'
            add_exception_custom_msg(e, error_msg)
            raise
    def __init__(self, img: Image, path: str, delay=False) -> None:
        self.delay = delay
        self.img_path = path

        if sys.platform != 'win32':
            if self.delay:
                self.bmp = None
            else:
                self.bmp = img.convert_to_wx_bitmap(wx)

        self._original_width = self.width = img.width
        self._original_height = self.height = img.height

        self.img = img
        self.zoomed_bmp = None
        self.rotation = 0

    def getImg(self) -> Any:
        return self.img

    def copy(self) -> Self:
        return FreeImage(self.img, self.img_path)
        
    def delayed_load(self) -> None:
        if not self.delay:
            log.debug("delayed_load was called but delay was off")
            return
        if sys.platform != 'win32':
            self.bmp = self.img.convert_to_wx_bitmap(wx)
            if self.zoomed_bmp:
                self.zoomed_bmp = self.zoomed_bmp.convert_to_wx_bitmap(wx)
        self.delay = False

    def rescale(self, width, height) -> Self:
        #TODO: Make sure this isn't called multiple times with the same dimensions.
        #I don't want to actually store this in zoomed_bmp, but something similar is fine.
        return self.img.rescale(width, height, fi.FILTER_BICUBIC)

    def resize(self, width: int, height: int) -> None:
        if self.base_width == width and self.base_height == height:
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

    def _do_rotate(self, clockwise: int) -> None:
        self.img = self.img.rotate(90 if clockwise else 270)
        if self.zoomed_bmp:
            if self.rotation in (1, 3):
                w, h = self.height, self.width
            else:
                w, h = self.width, self.height
            self.resize(w, h)
        else:
            self.width = self.base_width
            self.height = self.base_height
        
    def paint(self, dc: wx.DC, x: int, y: int) -> None:
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

    def copy_to_clipboard(self) -> None:
        if sys.platform == 'win32':
            #TODO: (2,2) Improve: there's a better way to do this with Win32 API
            #    (check FreeImagePlus's copy)
            bmp = self.img.convert_to_wx_bitmap(wx)
            super().do_copy_to_clipboard(bmp)
        else:
            super().do_copy_to_clipboard(self.bmp)

    def create_thumbnail(self, width: int, height: int, delay: bool = False) -> wx.Bitmap|Callable[[],wx.Bitmap]:
        (width, height) = self.get_thumbnail_size(width, height)
        img = self.img.rescale(width, height, fi.FILTER_BILINEAR)
        if delay:
            def delayed_fn(_img=img, _wx=wx) -> wx.Bitmap:
                return _img.convert_to_wx_bitmap(_wx)
            return delayed_fn
        else:
            bmp = img.convert_to_wx_bitmap(wx)
            return bmp

    @staticmethod
    def _get_extensions() -> list[str]:
        return [x.casefold() for x in fi.library.load().get_readable_extensions()]
    ext_list = _get_extensions()
    
    @staticmethod
    def extensions():
        return FreeImage.ext_list

    def close(self):
        pass
