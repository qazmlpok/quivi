import math

# wxcairo must be imported before wx. Do not change the import order.
from wx.lib import wxcairo

try:
    # noinspection PyUnusedImports
    import cairocffi
    cairocffi.install_as_pycairo()
    import cairo
    cairo_stride_for_width = cairo.ImageSurface.format_stride_for_width
except ImportError:
    import cairo
    cairo_stride_for_width = cairo.Format.stride_for_width
import wx
from cairo._cairo import ImageSurface
from quivilib.interface.imagehandler import *

log = logging.getLogger('cairo')


class CairoImage(ImageHandlerBase, SecondaryImageHandler):
    @classmethod
    def CreateImage(cls, f:IO[bytes], path:str, delay=False) -> ImageHandler:
        raise Exception("Use another class to open the image first")

    @classmethod
    def CreateWrappedImage(cls, src:ImageHandler|None=None, delay=False) -> ImageHandler:
        if src is None:
            raise Exception("Cairo must have a separate image loader.")
        if src.is_animated() and isinstance(src, AnimatedImage):
            return AnimatedCairoImage(src, delay=delay)
        return CairoImage(src, delay=delay)

    def __init__(self, src:ImageHandler, delay=False) -> None:
        self.src = src
        self.img_path = src.img_path
        img = self.convert_to_cairo_surface(src.getImg())
        
        self._original_width = self._width = img.get_width()
        self._original_height = self._height = img.get_height()
        
        self.img = img
        #Set by the thread
        self.zoomed_bmp: cairo.ImageSurface|None = None
        self.zoomed_width = None
        self.delay = delay
        self.rotation = 0
        
        self.timer: threading.Timer|None = None
        #Used to determine if the current paint action is a pan or a zoom.
        #Pans need to be significantly faster, and thus require a lower quality filter.
        self._last_zoom = 1.0
        self._last_rot = 0

    def copy(self) -> ImageHandler:
        return CairoImage(src=self.src)

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

    def convert_to_cairo_surface(self, img: BaseImageProt):
        """ Requests img data as bytes from the loaded image
        Loads that data in as a cairo surface. Should work with either image loader.
        """
        srcImage = img
        img_format = cairo.FORMAT_ARGB32
        width, height = img.width, img.height
        stride = cairo_stride_for_width(img_format, width)
        #TODO: I can't get other cairo formats to work. But if I could, this would need to report
        #the format, e.g. to allow changing to RGB24. See https://afrantzis.com/pixel-format-guide/cairo.html
        #or https://github.com/afrantzis/pixel-format-guide/blob/master/pfg/cairo.py
        img = img.maybeConvert32bit()
        b = img.convert_to_raw_bits(width_bytes=stride)
        surface = cairo.ImageSurface.create_for_data(b, img_format, width, height)
        
        if img is not srcImage:
            del img
        return surface

    def delayed_load(self):
        #The actual delay load is unncessary, but the flag is needed to know if this is waiting for actual display or not.
        self.delay = False

    def _delayed_resize(self, width: int, height: int):
        if self.zoomed_width == width or self._original_width == width:
            return
        zoomed = self._resize_img(width, height)
        if self._width == width and self._height == height:
            #Make sure this isn't an out of order execution.
            self.zoomed_bmp = zoomed
            self.zoomed_width = width
            log.debug(f"Cairo: Updated zoomed bitmap ({width}x{height})")
            if self.img_change_cb:
                self.img_change_cb(self)

    def _maybe_scale_image(self):
        #Always clear out the timer and previous scaled image, if set.
        self.zoomed_bmp = None
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
        if self.src.is_animated():
            #Disable this for now.
            return
        self.timer = timer = threading.Timer(0.2, self._delayed_resize, args=[self._width, self._height])
        timer.start()

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
            self._delayed_resize(self._width, self._height)
        else:
            self._maybe_scale_image()

    def _resize_img(self, width: int, height: int) -> ImageSurface:
        resized = self.src.rescale(width, height)
        ret = self.convert_to_cairo_surface(resized)
        #del resized
        return ret

    def resize_by_factor(self, factor: float) -> None:
        #Needs to use the non-rotated values as the image isn't actually rotated.
        width = int(self._original_width * factor)
        height = int(self._original_height * factor)
        self.resize(width, height)

    def _do_rotate(self, clockwise: int) -> None:
        #Do nothing - changing self.rotation is enough
        pass

    def get_display_surface(self) -> tuple[ImageSurface, bool]:
        """Returns the surface that should be drawn, and a bool indicating if this surface is already-zoomed.
        If the surface was generated by the background thread, it is already zoomed and that portion of the matrix should not be applied.
        For animated images, returns the appropriate animation frame.
        Cairo version of get_display_bitmap. """
        if self.zoomed_bmp:
            return (self.zoomed_bmp, True)
        return (self.img, False)

    def paint(self, dc: wx.DC, x: int, y: int) -> None:
        img, is_zoomed = self.get_display_surface()
        ctx = wxcairo.ContextFromDC(dc)
        imgpat = cairo.SurfacePattern(img)
        
        wscale = self._original_width  / self._width 
        hscale = self._original_height / self._height

        #Set quality for the scale. There are a few tricks that can be done with this.
        if (self._last_zoom != wscale or self._last_rot != self.rotation):
            #This is a zoom change - panning needs to be fast, but scaling doesn't.
            quality = cairo.FILTER_GOOD
        elif self._width > self._original_width:
            #Zooming in on a large image is faster than zooming out
            #This is kinda annoying, because the artifacts are a lot worse when zooming out.
            quality = cairo.FILTER_GOOD
        else:
            quality = cairo.FILTER_FAST
        self._last_zoom = wscale    #No real need to track both.
        self._last_rot = self.rotation
        #FAST - A high-performance filter, with quality similar to Cairo::Patern::Filter::NEAREST.
        #GOOD - A reasonable-performance filter, with quality similar to Cairo::BILINEAR.
        #BEST - The highest-quality available, performance may not be suitable for interactive use.

        matrix = cairo.Matrix()
        if not is_zoomed:
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
    
    def copy_to_clipboard(self) -> None:
        bmp = wxcairo.BitmapFromImageSurface(self.img)
        self.do_copy_to_clipboard(bmp)

    def create_thumbnail(self, width: int, height: int, delay: bool = False) -> wx.Bitmap|Callable[[],wx.Bitmap]:
        return self.src.create_thumbnail(width, height, delay)

    def set_callback(self, cb: Callable[[ImageHandler], None]):
        def wrapped_cb(who: ImageHandler):
            #For cairo, if the underlying image changes, that should trigger an update here
            #and then pass on the update.
            if self.img_change_cb:
                self.img_change_cb(self)
        self.src.set_callback(wrapped_cb)
        super().set_callback(cb)

    @staticmethod
    def extensions():
        """ Extensions do not matter for Cairo. """
        return []

class AnimatedCairoImage(CairoImage, AnimatedImage):
    def __init__(self, src: AnimatedImage, delay=False) -> None:
        CairoImage.__init__(self, src, delay)

        self.cairo_frames: list[ImageSurface] = []
        self.converted_cairo_frames: list[ImageSurface|None] = [None] * src.frame_count

        self.src = src
        # Calling this creates, but does not start, the timer.
        # The underlying image will manage the actual animation, so just don't call super.
        #AnimatedImage.__init__(self, src.frames, src.delays)

    def get_display_surface(self) -> tuple[ImageSurface, bool]:
        #Return the current frame.
        number = self.src.frame
        converted = self.converted_cairo_frames[number]
        if converted:
            return (converted, True)
        return (self.cairo_frames[number], False)

    def load_frames(self) -> None:
        #Do not call this on src.
        self.cairo_frames = [self.convert_to_cairo_surface(x.get_frame_img(x)) for x in self.src.frames]
        self.img = self.cairo_frames[0]

    def start_animation(self):
        #Start animating the underlying image
        self.src.start_animation()
    def stop_animation(self):
        #Stop animating the underlying image
        self.src.stop_animation()
    def close(self) -> None:
        super(CairoImage, self).close()
        self.src.close()

    def get_display_bmp(self):
        raise Exception("Should not be called - use get_display_surface instead.")
