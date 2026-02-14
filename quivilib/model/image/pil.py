import logging
from collections.abc import Callable
from typing import Any, IO, Self

import wx
from PIL import Image

from quivilib.interface.imagehandler import ImageHandlerBase

log: logging.Logger = logging.getLogger('pil')
#PIL has its own logging that's typically not relevant.
logging.getLogger("PIL").setLevel(logging.ERROR)


class PilWrapper():
    """ Wrapper class; used to store image data.
    Adds a few functions to be consistent with FreeImage.
    TODO: Add With support. Add an IsTemp to allow automatic disposal.
    some methods may create a temporary object, which can just be removed automatically.
    """
    @classmethod
    def allocate(cls: type['PilWrapper'], width, height, bpp, red_mask=0, green_mask=0, blue_mask=0) -> 'PilWrapper':
        #*_mask is for FI compatibility; they will be ignored.
        #Should be 8-bit monochrome
        #Note - this will only ever actually be called with 24
        mode = 'L'
        if bpp == 32:
            mode = 'RGBA'
        elif bpp == 24:
            mode = 'RGB'
        img = Image.new(mode, size=(width, height))
        return PilWrapper(img)
    def AllocateNew(self, *args, **kwargs) -> 'PilWrapper':
        """ Forward to static implementation. Needed for polymorphism.
        """
        return PilWrapper.allocate(*args, **kwargs)
        
    def __init__(self, img: Image.Image) -> None:
        self.img = img
        self.width = img.width
        self.height = img.height
    
    def __getattr__(self, name):
        return getattr(self.img, name)
        
    def getData(self) -> tuple[int, int, bytes]:
        b = self.img.tobytes()
        return (self.width, self.height, b)
    def maybeConvert32bit(self) -> 'PilWrapper':
        if self.img.mode != 'RGB':
            return PilWrapper(self.img.convert('RGB'))
        return self
    def convert_to_raw_bits(self, width_bytes=None) -> bytearray:
        #width_bytes is ignored. Should it be?
        im = self.img
        if 'A' not in im.getbands():
            im = im.copy()
            im.putalpha(256)
        arr = bytearray(im.tobytes('raw', 'BGRa'))
        if im is not self.img:
            del im
        return arr
    #Image operations; this needs to have the same interface as FI.
    def rescale(self, width: int, height: int) -> Self:
        #I think this needs to return self if the width/height are the same.
        img = self.img.resize((width, height), Image.Resampling.BICUBIC)
        return PilWrapper(img)
    def transpose(self, method: Image.Transpose) -> Self:
        img = self.img.transpose(method)
        return PilWrapper(img)
    def fill(self, color) -> None:
        (r, g, b) = color
        img = self.img
        img.paste( (r,g,b), (0, 0, img.size[0], img.size[1]))
        
    def paste(self, src, left: int, top: int, alpha: int = 256) -> None:
        #I honestly have no idea what the FI code is doing or if it's needed.
        img = self.img
        srcimg = src.img
        img.paste(srcimg, (left, top, srcimg.size[0] + left, srcimg.size[1] + top))

    def copy_region(self, left: int, top: int, right: int, bottom: int) -> Self:
        #The freeimage copy function will also crop. PIL's copy is just a straight copy.
        img = self.img
        copy = img.crop((left, top, right, bottom,))
        return PilWrapper(copy)
    def save_bitmap(self, path):
        #FI needs a constant; this is exposed as a separate member for compatibility
        return self.save(path)
    def save(self, path) -> None:
        #Type will be determined by path; there's no need to specify manually.
        self.img.save(path)
    def __del__(self) -> None:
        if self.img:
            del self.img

class PilImage(ImageHandlerBase):
    @classmethod
    def CreateImage(cls, f:IO[bytes], path:str, delay=False) -> Self:
        #Used to convert 16-bit int precision images to 8-bit.
        #PIL's behavior is to truncate, which is not useful.
        #Remove this if that ever changes. It's been reported, and it sounds like they
        #stopped truncating, but it's still doing it.
        def lookup(x):
            return x / 256

        img = Image.open(f)
        if img.mode[0] == 'I':    #16-bit precision
            img = img.point(lookup, 'RGB')
        elif img.mode != 'RGB':
            img = img.convert('RGB')

        return PilImage(img, delay=delay)
    def __init__(self, img: Image.Image, delay=False) -> None:
        self.delay = delay

        self.bmp: wx.Bitmap = self._img_to_bmp(img)
        
        self._original_width = self.width = img.size[0]
        self._original_height = self.height = img.size[1]
        
        self.img = PilWrapper(img)
        self.zoomed_bmp: wx.Bitmap|None = None
        self.delayed_bmp: tuple[int, int, bytes]|None = None
        self.rotation = 0

    def getImg(self) -> Any:
        return self.img

    def copy(self) -> Self:
        return PilImage(img=self.img.img)
        
    def delayed_load(self) -> None:
        if not self.delay:
            log.debug("delayed_load was called but delay was off")
            return
        self.bmp = wx.Bitmap.FromBuffer(self.img.size[0], self.img.size[1], self.bmp)
        if self.delayed_bmp:
            w, h, s = self.delayed_bmp
            self.zoomed_bmp = wx.Bitmap.FromBuffer(w, h, s)
            self.delayed_bmp = None
        self.delay = False
    
    def _img_to_bmp(self, img):
        s = img.tobytes()
        if self.delay:
            return s
        else:
            return wx.Bitmap.FromBuffer(img.size[0], img.size[1], s)
    
    def rescale(self, width: int, height: int) -> Self:
        #Wrapper (needed for Cairo)
        return self.img.rescale(width, height)
    def resize(self, width: int, height: int) -> None:
        if self.base_width == width and self.base_height == height:
            self.zoomed_bmp = None
        else:
            wrapper = self.img.rescale(width, height)
            (w, h, s) = wrapper.getData()
            if self.delay:
                #TODO: Consider always making the delayed load a tuple and always use _img_to_bmp
                self.delayed_bmp = (w, h, s)
            else:
                self.zoomed_bmp = wx.Bitmap.FromBuffer(w, h, s)
        self.width = width
        self.height = height

    def _do_rotate(self, clockwise: int) -> None:
        self.img = self.img.transpose(Image.Transpose.ROTATE_90 if clockwise else Image.Transpose.ROTATE_270)
        #Update the bmp
        self.bmp = self._img_to_bmp(self.img)
        #Rotate the stored dimensions for any future/current zoom operations
        self.width, self.height = (self.height, self.width)
        
    def paint(self, dc: wx.DC, x: int, y: int) -> None:
        if self.delay:
            log.error("paint called but image was not loaded")
            return
        bmp = self.zoomed_bmp if self.zoomed_bmp else self.bmp
        dc.DrawBitmap(bmp, x, y)

    def create_thumbnail(self, width: int, height: int, delay: bool) -> wx.Bitmap|Callable[[],wx.Bitmap]:
        (width, height) = self.get_thumbnail_size(width, height)
        img = self.img.resize((width, height), Image.Resampling.BICUBIC)
        bmp = wx.Bitmap.FromBuffer(width, height, img.tobytes())
        #TODO: Implement delayed_fn. See freeimage.
        return bmp

    @staticmethod
    def _get_extensions() -> list[str]:
        return [x.casefold() for x in Image.registered_extensions().keys()]
    ext_list: Any = _get_extensions()
    
    @staticmethod
    def extensions():
        return PilImage.ext_list

    def close(self) -> None:
        pass
