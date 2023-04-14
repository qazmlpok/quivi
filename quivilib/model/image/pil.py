

from quivilib.util import rescale_by_size_factor

from PIL import Image
import logging
log = logging.getLogger('pil')
#PIL has its own logging that's typically not relevant.
logging.getLogger("PIL").setLevel(logging.ERROR)

import wx



class PilWrapper():
    """ Wrapper class; used to store image data.
    Adds a few functions to be consistent with FreeImage.
    TODO: Add With support. Add an IsTemp to allow automatic disposal.
    some methods may create a temporary object, which can just be removed automatically.
    """
    def __init__(self, img):
        self.img = img
        self.width = img.width
        self.height = img.height
    
    def __getattr__(self, name):
        return getattr(self.img, name)
        
    def getData(self):
        bytes = self.img.tobytes()
        return (self.width, self.height, bytes)
    def maybeConvert32bit(self):
        if self.img.mode != 'RGB':
            return PilWrapper(self.img.convert('RGB'))
        return self
    def convert_to_raw_bits(self, width_bytes=None):
        #width_bytes is ignored. Should it be?
        im = self.img
        if 'A' not in im.getbands():
            im = im.copy()
            im.putalpha(256)
        arr = bytearray(im.tobytes('raw', 'BGRa'))
        if im is not self.img:
            del im
        return arr
    def rescale(self, width, height):
        #I think this needs to return self if the width/height are the same.
        img = self.img.resize((width, height), Image.BICUBIC)
        return PilWrapper(img)
    def __del__(self):
        if self.img:
            del self.img

class PilImage(object):
    def __init__(self, canvas_type, f=None, path=None, img=None, delay=False):
        self.canvas_type = canvas_type
        self.delay = delay
        
        if img is None:
            img = Image.open(f)
            if img.mode != 'RGB':
                img = img.convert('RGB')
        
        self.bmp = self._img_to_bmp(img)
        
        self.original_width = self.width = img.size[0]
        self.original_height = self.height = img.size[1]
        
        self.img = PilWrapper(img)
        self.zoomed_bmp = None
        self.rotation = 0
        
    def delayed_load(self):
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
    
    def rescale(self, width, height):
        #Wrapper (needed for Cairo)
        return self.img.rescale(width, height)
    def resize(self, width, height):
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

    def resize_by_factor(self, factor):
        width = int(self.original_width * factor)
        height = int(self.original_height * factor)
        self.resize(width, height)
        
    def rotate(self, clockwise):
        self.rotation += (1 if clockwise else -1)
        self.rotation %= 4
        self.img = self.img.transpose(Image.ROTATE_90 if clockwise else Image.ROTATE_270)
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
        
    def paint(self, dc, x, y):
        if self.delay:
            log.error("paint called but image was not loaded")
            return
        bmp = self.zoomed_bmp if self.zoomed_bmp else self.bmp
        dc.DrawBitmap(bmp, x, y)

    def copy(self):
        return PilImage(img=self.img)
    
    def copy_to_clipboard(self):
        data = wx.BitmapDataObject(self.bmp)
        if wx.TheClipboard.Open():
            wx.TheClipboard.SetData(data)
            wx.TheClipboard.Close()

    def create_thumbnail(self, width, height, delay):
        factor = rescale_by_size_factor(self.original_width, self.original_height, width, height)
        if factor > 1:
            factor = 1
        width = int(self.original_width * factor)
        height = int(self.original_height * factor)
        img = self.img.resize((width, height), Image.BICUBIC)
        bmp = wx.Bitmap.FromBuffer(width, height, img.tobytes())
        #TODO: Implement delayed_fn. See freeimage.
        return bmp

    def _get_extensions():
        return list(Image.registered_extensions().keys())
    ext_list = _get_extensions()
    
    def extensions():
        return PilImage.ext_list

    def close(self):
        pass
