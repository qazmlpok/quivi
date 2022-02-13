

from quivilib.util import rescale_by_size_factor

from PIL import Image
import logging
log = logging.getLogger('pil')

import wx



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
        
        self.img = img
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
    
    def resize(self, width, height):
        if self.original_width == width and self.original_height == height:
            self.zoomed_bmp = None
        else:
            img = self.img.resize((width, height), Image.BICUBIC)
            w, h = img.size
            s = img.tobytes()
            del img
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

    def close(self):
        pass
