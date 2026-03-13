from collections.abc import Callable
from typing import Protocol, IO, Self, Tuple, List

import wx

from quivilib.util import rescale_by_size_factor


#
import time


class BaseImageProt(Protocol):
    """Protocol for an image, direct from PIL/FreeImage.
    Or, rather, the wrapper classes used to standardize the interface."""
    width: int
    height: int

    def save_bitmap(self, path: str):
        pass

    def rescale(self, width: int, height: int) -> Self:
        pass

    def AllocateNew(self, *args, **kwargs) -> Self:
        pass

    def maybeConvert32bit(self) -> Self:
        pass

    def convert_to_raw_bits(self, width_bytes=None) -> bytearray:
        pass

    def copy_region(self, left: int, top: int, right: int, bottom: int) -> Self:
        pass

    def paste(self, src, left: int, top: int, alpha: int = 256) -> None:
        pass

    def fill(self, color) -> None:
        pass

class ImageHandler(Protocol):
    """ Interface for a generic image.
    The actual Image class for the appropriate handler (i.e. Freeimage or PIL) will expose a common set of operations.
    """
    @classmethod
    def CreateImage(cls, f:IO[bytes], path:str, delay=False) -> Self:
        """Static constructor. Create a new image object."""
        pass
    @classmethod
    def OpenImage(cls, f:IO[bytes], path:str, delay=False) -> BaseImageProt:
        """Create a new image of the appropriate type. This bypasses the ImageHandler stuff.
        Used for direct access to the image data."""
        pass
    def delayed_load(self) -> None:
        """Image loading can be deferred (i.e. for the cache). Calling this modifies local state to prepare the image data for actual display."""
        pass
    def resize_by_factor(self, factor: float) -> None:
        """Resize the image to a specific zoom level. Modifies the local image."""
        pass
    def rotate(self, clockwise: int) -> None:
        """Rotate the image in 90 degree increments (clockwise or counter). Modifies the local image."""
        pass
    def rescale(self, width: int, height: int) -> Self:
        """Create a new image with the given width/height."""
        pass
    def paint(self, dc: wx.DC, x: int, y: int) -> None:
        """Draw onto the wx DrawingContext"""
        pass
    def copy(self) -> Self:
        pass
    def copy_to_clipboard(self) -> None:
        pass
    def create_thumbnail(self, width: int, height: int, delay: bool) -> wx.Bitmap|Callable[[],wx.Bitmap]:
        pass
    def set_callback(self, cb: Callable[[Self], None]):
        """Set a callback to be fired if the underlying image changes. Used for the cairo "fast zoom" delayed load.
        This doesn't use pubsub because the owning canvas needs to know if the event should be ignored or not."""
        pass
    def start_animation(self):
        """(Animated images only) Start the animation. Must be called on the main thread."""
        pass
    def stop_animation(self):
        """(Animated images only) Stop the animation."""
        pass

    width: int
    "The current width of the displayed image"
    height: int
    "The current height of the displayed image"

    img_path: str
    "Path to the image. Intended for debugging only. Not referenced."

    def is_animated(self) -> bool:
        pass

    def close(self) -> None:
        pass

    @property
    def base_width(self) -> int:
        """The width of the originally loaded image, _before_ rescaling, but _after_ rotation.
        Used to calculate fit-to-screen"""
        pass

    @property
    def base_height(self) -> int:
        """The height of the originally loaded image, _before_ rescaling, but _after_ rotation.
        Used to calculate fit-to-screen"""
        pass
    
    @staticmethod
    def extensions() -> list[str]:
        pass
    def getImg(self) -> BaseImageProt:
        """Direct access to the underlying Image, which is likely a mistake."""
        pass

class SecondaryImageHandler(ImageHandler):
    @classmethod
    def CreateWrappedImage(cls, src: ImageHandler | None = None, delay=False) -> ImageHandler:
        pass

class ImageHandlerBase(ImageHandler):
    """(Abstract) Base class for concrete implementations of ImageHandler.
    Handles some shared logic common to images that does not rely on the underlying implementation.
    Declares some common properties that aren't exposed in the interface"""
    bmp: wx.Bitmap
    rotation: int
    """Current rotation, in 90-degree increments. Must be [0,3]."""
    _original_width: int
    "Width of the originally loaded image, without modification"
    _original_height: int
    "Height of the originally loaded image, without modification"
    img_change_cb: Callable[[ImageHandler], None] | None = None
    "Callback function used to inform the owning canvas of a change to the image"

    @property
    def base_width(self):
        """The width of the originally loaded image, _before_ rescaling, but _after_ rotation.
        Used to calculate fit-to-screen"""
        if self.rotation in (0, 2):
            return self._original_width
        return self._original_height

    @property
    def base_height(self):
        """The height of the originally loaded image, _before_ rescaling, but _after_ rotation.
        Used to calculate fit-to-screen"""
        if self.rotation in (0, 2):
            return self._original_height
        return self._original_width

    def _do_rotate(self, clockwise: int):
        """Rotate the image. Modifies self.img"""
        #Implemented in subclasses.
        pass

    def rotate(self, clockwise: int) -> None:
        self.rotation += (1 if clockwise else -1)
        self.rotation %= 4
        self._do_rotate(clockwise)

    def resize(self, width: int, height: int) -> None:
        pass

    def resize_by_factor(self, factor: float) -> None:
        width = int(self.base_width * factor)
        height = int(self.base_height * factor)
        self.resize(width, height)

    def get_thumbnail_size(self, width, height) -> Tuple[int, int]:
        factor = rescale_by_size_factor(self.base_width, self.base_height, width, height)
        factor = min(factor, 1)
        width = int(self.base_width * factor)
        height = int(self.base_height * factor)
        return (width, height)

    def copy_to_clipboard(self) -> None:
        self.do_copy_to_clipboard(self.bmp)

    def do_copy_to_clipboard(self, bmp: wx.Bitmap) -> None:
        data = wx.BitmapDataObject(bmp)
        if wx.TheClipboard.Open():
            wx.TheClipboard.SetData(data)
            wx.TheClipboard.Close()

    def get_display_bmp(self) -> wx.Bitmap:
        """Returns the bitmap that should be drawn.
        Used to deal with logic around animations and zooming."""
        pass

    def is_animated(self):
        return False

    def set_callback(self, cb:Callable[[Self], None]):
        self.img_change_cb = cb

    def close(self) -> None:
        pass

class AnimatedImage(ImageHandlerBase):
    """Base class for an animated image. Manages a timer to handle the animation, using the callback function to report changes.
    delays should be a list of duration in ms (GIF stores the value in cs)
    """
    def __init__(self, frames: List[wx.Bitmap], delays: List[int], loops = 0):
        if len(frames) != len(delays):
            raise Exception("Frames and Delays must have the same number of entries.")
        if len(frames) < 2:
            #Caller should guard against this. I'm sure it's possible to create a 1-frame animated gif.
            raise Exception("Animated image must have at least 2 frames.")
        #Frames:
        #For direct rendering, I need wx.Bitmaps.
        #For cairo, I need something that implements convert_to_raw_bits (freeimage does this through the dll. PIL uses a wrapper)

        self.frame = 0
        self.frames = frames
        self.delays = delays
        self.max_loops = loops

        self.all_same = all(x == delays[0] for x in delays)
        self.handler = wx.EvtHandler()
        self.timer = wx.Timer(self.handler)
        self.handler.Bind(wx.EVT_TIMER, self._next_frame, self.timer)

        self.sleep_offset = 2

        if __debug__:
            self.loop_total = sum(self.delays)
            self.start = 0.0
            self.planned_delay = 0#
            self.real_delay = time.perf_counter()#

    def get_display_bmp(self):
        #Animated images just won't support zooming, at least unless cairo can be used.
        return self.frames[self.frame]

    def start_animation(self):
        """Start the animation. This must be called on the main thread for wx.Timer to work."""
        self.frame = 0
        if self.all_same:
            #Assumption: a repeating timer will have less jitter than firing off multiple OneShot timers.
            #-Jitter appears to be roughly 2% (with 20-30ms frame delays). The persistent timer is not actually performing better.
            self.timer.Start(self.delays[0])
        else:
            self.planned_delay = self.delays[self.frame]
            self.real_delay = time.perf_counter()
            self.timer.Start(self.delays[self.frame] - self.sleep_offset, True)
        if __debug__:
            self.start = time.perf_counter()
            print(f"Expected loop duration: {self.loop_total}ms.")

    def stop_animation(self):
        self.timer.Stop()

    def _next_frame(self, event):
        """Advance the image to the next frame, or back to the first one. Fire the callback."""
        stop = time.perf_counter()
        if (self.sleep_offset != 0 and (stop - self.real_delay) * 1000 < self.planned_delay):
            delay = (self.planned_delay - ((stop - self.real_delay) * 1000)) / 1000.0
            print(f"Sleep an additional {delay}s")
            time.sleep(delay)

        self.frame = (self.frame + 1) % len(self.frames)
        if __debug__ and self.frame == 0:
            stop = time.perf_counter()
            print(f" ---> Loop complete. took: {(stop - self.start)*1000:0.1f}ms. {((stop - self.start)*1000.0) / self.loop_total * 100:0.1f}%")
            self.start = time.perf_counter()

        #changing self.frame will change the image paint() uses.
        self.img_change_cb(self)
        if not self.all_same:
            stop = time.perf_counter()
            #TODO: Should this attempt to compensate for jitter at all?
            print(f"Frame took: {(stop - self.real_delay) * 1000:0.1f}ms. Plan: {self.planned_delay}. {(stop - self.real_delay) / self.planned_delay * 100 * 1000:0.1f}%.")

            self.planned_delay = self.delays[self.frame]
            self.timer.Start(self.delays[self.frame] - self.sleep_offset, True)
            self.real_delay = time.perf_counter()

    def duration_to_time(self, value: int) -> int:
        """
        GIF encodes per-frame delays in increments of 0.01s (i.e. 10ms or 1cs). Browsers will not perfectly obey this.
        In practice it looks like too-small values are moved up to 100ms, so a delay of "1" is slower than "2".
        This is for GIF specifically; it's possible APNG/WEBM have different logic.
        In theory this is browser-specific but every browser I tested had the same behavior.
        Ref: https://www.tumblr.com/pharanpostsartndevtrivia/126581964275/how-is-an-animated-gifs-time-delay-between
        NOTE - input time needs to be in ms. PIL at least standardizes this.
        """
        if value < 20:
            return 100
        return value

    def is_animated(self):
        return True

    def close(self) -> None:
        super().close()
        self.stop_animation()
