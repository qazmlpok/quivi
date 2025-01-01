import logging
import wx
from PIL import Image
from quivilib.util import rescale_by_size_factor
from quivilib.model.image.interface import ImageHandler

from typing import Any, TypeVar, IO

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
        
    def getData(self) -> tuple[Any, Any, Any]:
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
    def rescale(self, width: int, height: int) -> 'PilWrapper':
        #I think this needs to return self if the width/height are the same.
        img = self.img.resize((width, height), Image.Resampling.BICUBIC)
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

    def copy_region(self, left: int, top: int, right: int, bottom: int) -> 'PilWrapper':
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

class PilImage(ImageHandler):
    def __init__(self, f:IO[bytes]|None=None, path:str|None=None, img=None, delay=False) -> None:
        self.delay = delay

        #Used to convert 16-bit int precision images to 8-bit.
        #PIL's behavior is to truncate, which is not useful.
        #Remove this if that ever changes. It's been reported, and it sounds like they
        #stopped truncating, but it's still doing it.
        def lookup(x):
            return x / 256

        if img is None and f is not None:
            img = Image.open(f)
            if img.mode == 'I':    #16-bit precision
                #return img.point(PilImage.PixelLookup, 'RGB')
                img = img.point(lookup, 'RGB')
            elif img.mode != 'RGB':
                img = img.convert('RGB')
        
        self.bmp = self._img_to_bmp(img)
        
        self.original_width = self.width = img.size[0]
        self.original_height = self.height = img.size[1]
        
        self.img = PilWrapper(img)
        self.zoomed_bmp: tuple[int, int, int]|None = None
        self.rotation = 0
        
    def delayed_load(self) -> None:
        if not self.delay:
            log.debug("delayed_load was called but delay was off")
            return
        self.bmp = wx.Bitmap.FromBuffer(self.img.size[0], self.img.size[1], self.bmp)
        if self.zoomed_bmp:
            w, h, s = self.zoomed_bmp
            self.zoomed_bmp = wx.Bitmap.FromBuffer(w, h, s)
        self.delay = False
    
    def _img_to_bmp(self, img):
        s = img.tobytes()
        if self.delay:
            return s
        else:
            return wx.Bitmap.FromBuffer(img.size[0], img.size[1], s)
    
    def rescale(self, width: int, height: int):
        #Wrapper (needed for Cairo)
        return self.img.rescale(width, height)
    def resize(self, width: int, height: int) -> None:
        if self.original_width == width and self.original_height == height:
            self.zoomed_bmp = None
        else:
            wrapper = self.img.rescale(width, height)
            (w, h, s) = wrapper.getData()
            if self.delay:
                #TODO: Consider always making the delayed load a tuple and always use _img_to_bmp
                self.zoomed_bmp = (w, h, s)
            else:
                self.zoomed_bmp = wx.Bitmap.FromBuffer(w, h, s)
        self.width = width
        self.height = height

    def resize_by_factor(self, factor: float) -> None:
        width = int(self.original_width * factor)
        height = int(self.original_height * factor)
        self.resize(width, height)
        
    def rotate(self, clockwise: int) -> None:
        self.rotation += (1 if clockwise else -1)
        self.rotation %= 4
        self.img = self.img.transpose(Image.Transpose.ROTATE_90 if clockwise else Image.Transpose.ROTATE_270)
        #Update the bmp
        self.bmp = self._img_to_bmp(self.img)
        #Rotate the stored dimensions for any future/current zoom operations
        self.width, self.height = (self.height, self.width)
        self.original_width, self.original_height = (self.original_height, self.original_width)
        if self.zoomed_bmp:
            #Update the zoomed bmp
            #TODO: the calling function may call resize_by_factor as part of the adjust,
            #which makes this unnecessary. But this would need to be predicted.
            self.resize(self.width, self.height)
        
    def paint(self, dc, x: int, y: int) -> None:
        if self.delay:
            log.error("paint called but image was not loaded")
            return
        bmp = self.zoomed_bmp if self.zoomed_bmp else self.bmp
        dc.DrawBitmap(bmp, x, y)

    def copy(self) -> ImageHandler:
        return PilImage(img=self.img.img)
    
    def copy_to_clipboard(self) -> None:
        data = wx.BitmapDataObject(self.bmp)
        if wx.TheClipboard.Open():
            wx.TheClipboard.SetData(data)
            wx.TheClipboard.Close()

    def create_thumbnail(self, width: int, height: int, delay: bool):
        factor = rescale_by_size_factor(self.original_width, self.original_height, width, height)
        factor = min(factor, 1)
        width = int(self.original_width * factor)
        height = int(self.original_height * factor)
        img = self.img.resize((width, height), Image.Resampling.BICUBIC)
        bmp = wx.Bitmap.FromBuffer(width, height, img.tobytes())
        #TODO: Implement delayed_fn. See freeimage.
        return bmp

    @staticmethod
    def _get_extensions() -> list[str]:
        return list(Image.registered_extensions().keys())
    ext_list: Any = _get_extensions()
    
    @staticmethod
    def extensions():
        return PilImage.ext_list

    def close(self) -> None:
        pass

