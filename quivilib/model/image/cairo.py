import threading
import math
import logging

from wx.lib import wxcairo
import cairo
import wx
from quivilib.model.image.interface import ImageHandler
from quivilib.util import rescale_by_size_factor

log = logging.getLogger('cairo')


class CairoImage(ImageHandler):
    def __init__(self, canvas_type, src=None, img=None, delay=False):
        self.canvas_type = canvas_type
        
        if src is None:
            raise Exception("Cairo must have a separate image loader.")
            #if img.transparent:
            #    img = img.composite(True)
            #img = img.convert_to_32_bits()
        self.src = src
        img = self.convert_to_cairo_surface(src.img)
        width = img.get_width()
        height = img.get_height()
        
        self._original_width = self._width = width
        self._original_height = self._height = height
        
        self.img = img
        #Set by the thread
        self.zoomed_bmp = None
        self.zoomed_width = None
        self.delay = delay
        self.rotation = 0
        
        self.timer = None
        #Used to determine if the current paint action is a pan or a zoom.
        #Pans need to be significantly faster, and thus require a lower quality filter.
        self.last_zoom = 0
        self.last_rot = 0

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
    
    def convert_to_cairo_surface(self, img):
        """ Requests img data as bytes from the loaded image
        Loads that data in as a cairo surface. Should work with either image loader.
        """
        srcImage = img
        img_format = cairo.Format.ARGB32
        width, height = img.width, img.height
        stride = img_format.stride_for_width(width)
        #Make sure PIL and FreeImage both have this.
        #TODO: I can't get other cairo formats to work. But if I could, this would need to report
        #the format, e.g. to allow changing to RGB24. See https://afrantzis.com/pixel-format-guide/cairo.html
        #or https://github.com/afrantzis/pixel-format-guide/blob/master/pfg/cairo.py
        img = img.maybeConvert32bit()
        #Make sure PIL and FreeImage both have this.
        b = img.convert_to_raw_bits(width_bytes=stride)
        surface = cairo.ImageSurface.create_for_data(b, img_format, width, height)
        
        if img is not srcImage:
            del img
        return surface
    
    def delayed_load(self):
#        if not self.delay:
#            log.debug("delayed_load was called but delay was off")
#            return
#        if self.zoomed_bmp:
#            canvas = self.zoomed_bmp
#            self.zoomed_bmp = self._resize_img(w, h)
        self.delay = False

    #TODO: This should trigger a paint event (i.e. canvas.changed), but there's no existing way to do this here
    #and I don't think it's worth it to try and work around this.
    def delayed_resize(self, width, height):
        if self.zoomed_width == width or self._original_width == width:
            return
        zoomed = self._resize_img(width, height)
        if self._width == width and self._height == height:
            #Make sure this isn't an out of order execution.
            self.zoomed_bmp = zoomed
            self.zoomed_width = width
    def maybe_scale_image(self):
        #Always clear out the timer and previous scaled image, if set.
        #if self.timer is not None:
        self.zoomed_bmp = None      #if?
        self.zoomed_width = None
        if self.timer is not None:
            self.timer.cancel()
            self.timer = None
        #TODO: Maybe add other checks. There are various situations where there's no point in making a resized image
        if (self._width == self._original_width or self._height == self._original_height):
            return
        if (self._width > self._original_width):
            #Don't resize if zooming in. Need to figure out an appropriate cutoff
            #In practice this is probably dependent on screen size.
            return
        self.timer = threading.Timer(0.2, self.delayed_resize, args=[self._width, self._height])
        self.timer.start()

    def resize(self, width: int, height: int) -> None:
        #The actual resizing will be done on-demand by a matrix transformation.
        self._width = width
        self._height = height
        #0.2 seconds after this is called, create a real resized image.
        #Scaling via matrix is super quick. Panning a scaled image is not, unless low quality filter is used.
        #This is intended as a compromise - do the initial scale quickly, in a background thread, create a higher-quality scaled image
        #This should avoid both the stuttering from rapid resizing and from panning a scaled image.
        if self.delay:
            #This is still in the cache - immediately create the resized image in the current (cache) thread.
            self.delayed_resize(self._width, self._height)
        else:
            self.maybe_scale_image()

    def _resize_img(self, width, height):
        resized = self.src.rescale(width, height)
        ret = self.convert_to_cairo_surface(resized)
        #del resized
        return ret
        
    def resize_by_factor(self, factor: float) -> None:
        width = int(self._original_width * factor)
        height = int(self._original_height * factor)
        self.resize(width, height)
        
    def rotate(self, clockwise: int) -> None:
        self.rotation += (1 if clockwise else -1)
        self.rotation %= 4

    def paint(self, dc, x: int, y: int) -> None:
        img = self.zoomed_bmp if self.zoomed_bmp else self.img
        ctx = wxcairo.ContextFromDC(dc)
        imgpat = cairo.SurfacePattern(img)
        
        wscale = self._original_width  / self._width 
        hscale = self._original_height / self._height

        #Set quality for the scale. There are a few tricks that can be done with this.
        if (self.last_zoom != wscale or self.last_rot != self.rotation):
            #This is a zoom change - panning needs to be fast, but scaling doesn't.
            quality = cairo.Filter.GOOD
        elif self._width > self._original_width:
            #Zooming in on a large image is faster than zooming out
            #This is kinda annoying, because the artifacts are a lot worse when zooming out.
            quality = cairo.Filter.GOOD
        else:
            quality = cairo.Filter.FAST
        self.last_zoom = wscale    #No real need to track both.
        self.last_rot = self.rotation
        #FAST - A high-performance filter, with quality similar to Cairo::Patern::Filter::NEAREST.
        #GOOD - A reasonable-performance filter, with quality similar to Cairo::BILINEAR.
        #BEST - The highest-quality available, performance may not be suitable for interactive use.

        matrix = cairo.Matrix()
        if img == self.img:
            matrix.scale(wscale, hscale)
            #I believe this has no effect if the scale isn't done. Rotation is always 90 degrees, which I assume is optimized.
            imgpat.set_filter(quality)

        if self.rotation != 0:
            matrix.translate(self._width / 2, self._height / 2)
            matrix.rotate((0, 3.0 * math.pi / 2.0, math.pi, math.pi / 2.0)[self.rotation])
            if self.rotation in (0, 2):
                matrix.translate(-self._width / 2, -self._height / 2)
            else:
                matrix.translate(-self._height / 2, -self._width / 2)

        imgpat.set_matrix(matrix)
        ctx_matrix = cairo.Matrix()
        ctx_matrix.translate(x, y)
        ctx.set_matrix(ctx_matrix)
        
        ctx.set_source(imgpat)
        ctx.paint()

    def copy(self) -> ImageHandler:
        return CairoImage(self.canvas_type, img=self.img, src=self.src)
    
    def copy_to_clipboard(self) -> None:
        bmp = wxcairo.BitmapFromImageSurface(self.img)
        data = wx.BitmapDataObject(bmp)
        if wx.TheClipboard.Open():
            wx.TheClipboard.SetData(data)
            wx.TheClipboard.Close()

    def create_thumbnail(self, width: int, height: int, delay: bool = False):
        return self.src.create_thumbnail(width, height, delay)

    def close(self):
        pass
