
from quivilib.util import rescale_by_size_factor

import wx
from wx.lib import wxcairo
import pyfreeimage as fi
from pyfreeimage import Image
import cairo

import math
import logging

log = logging.getLogger('cairo')


class CairoImage(object):
    def __init__(self, canvas_type, f=None, path=None, img=None, delay=False):
        self.canvas_type = canvas_type
        
        if img is None:
            fi.library.load().reset_last_error()
            img = Image.load_from_file(f, path)
            try:
                if img.transparent:
                    img = img.composite(True)
            except RuntimeError:
                pass
            #img = img.convert_to_32_bits()
            img = img.convert_to_cairo_surface(cairo)
            
        width = img.get_width()
        height = img.get_height()
        
        self._original_width = self._width = width
        self._original_height = self._height = height
        
        self.img = img
        self.delay = delay
        self.rotation = 0
        
    @property
    def width(self):
        if self.rotation in (0, 2):
            return self._width
        return self._height

    @property
    def height(self):
        if self.rotation in (0, 2):
            return self._height
        return self._width
        
    @property
    def original_width(self):
        if self.rotation in (0, 2):
            return self._original_width
        return self._original_height

    @property
    def original_height(self):
        if self.rotation in (0, 2):
            return self._original_height
        return self._original_width
        
    def delayed_load(self):
#        if not self.delay:
#            log.debug("delayed_load was called but delay was off")
#            return
#        if self.zoomed_bmp:
#            canvas = self.zoomed_bmp
#            self.zoomed_bmp = self._resize_img(w, h)
        self.delay = False
        
    def resize(self, width, height):
        #The actual resizing will be done on-demand by a matrix transformation.
        self._width = width
        self._height = height
        
    def _resize_img(self, width, height):
        imgpat = cairo.SurfacePattern(self.img)
        scaler = cairo.Matrix()
        scaler.scale(self._original_width / float(width), self._original_height / float(height))
        imgpat.set_matrix(scaler)
        imgpat.set_filter(cairo.FILTER_BEST)
        canvas = cairo.ImageSurface(cairo.FORMAT_ARGB32, width, height)
        ctx = cairo.Context(canvas)
        ctx.set_source(imgpat)
        ctx.paint()
        return canvas
        
    def resize_by_factor(self, factor):
        width = int(self._original_width * factor)
        height = int(self._original_height * factor)
        self.resize(width, height)
        
    def rotate(self, clockwise):
        self.rotation += (1 if clockwise else -1)
        self.rotation %= 4
        
    def paint(self, dc, x, y):
        #TODO: Restore zoom_bmp.
        img = self.img
        ctx = wxcairo.ContextFromDC(dc)
        imgpat = cairo.SurfacePattern(img)
        
        matrix = cairo.Matrix()
        wscale = self._width / self._original_width
        hscale = self._height / self._original_height
        matrix.scale(wscale, hscale)

        if self.rotation != 0:
            matrix.translate(self._width / 2, self._height / 2)
            matrix.rotate((0, 3.0 * math.pi / 2.0, math.pi, math.pi / 2.0)[self.rotation])
            if self.rotation in (0, 2):
                matrix.translate(-self._width / 2, -self._height / 2)
            else:
                matrix.translate(-self._height / 2, -self._width / 2)

        matrix.translate(x / wscale, y / hscale)
        
        #BEST is too slow; this still looks fine.
        imgpat.set_filter(cairo.Filter.GOOD)
        ctx.set_matrix(matrix)

        #Clip image - doesn't seem to help. It's faster for zoomed-in images, so I suspect it's completely redundant.
        #Cairo is probably smart enough to not render past the DC edge.
        #if (self._width > self._original_width):
        #Clip if zoomed in. My assumption is this won't be as useful if zooming out (more of original image needed)
        #start = (x / wscale, y / hscale)
        #Can I get the dc dimensions?
        #end = (1920 / wscale, 1080 / hscale)
        #ctx.rectangle(-start[0], -start[1], end[0], end[1])
        #ctx.clip()
        
        ctx.set_source(imgpat)
        ctx.paint()

    def copy(self):
        return CairoImage(self.canvas_type, img=self.img)
    
    def copy_to_clipboard(self):
        bmp = wxcairo.BitmapFromImageSurface(self.img)
        data = wx.BitmapDataObject(bmp)
        if wx.TheClipboard.Open():
            wx.TheClipboard.SetData(data)
            wx.TheClipboard.Close()

    def create_thumbnail(self, width, height, delay=False):
        factor = rescale_by_size_factor(self.original_width, self.original_height, width, height)
        if factor > 1:
            factor = 1
        width = int(self.original_width * factor)
        height = int(self.original_height * factor)
        
        #This should actually still resize the image.
        thumb_canvas = self._resize_img(width, height)
        
        def delayed_load(thumb_canvas=thumb_canvas, width=width, height=height, wx=wx):
            return wxcairo.BitmapFromImageSurface(thumb_canvas)
        
        if delay:
            return delayed_load
        else:
            return delayed_load()

    #FreeImage is used to load the actual file.
    def _get_extensions():
        return fi.library.load().get_readable_extensions()
    ext_list = _get_extensions()
    def extensions():
        return CairoImage.ext_list

    def close(self):
        pass
