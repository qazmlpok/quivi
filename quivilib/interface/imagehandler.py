from collections.abc import Callable
from typing import Protocol, Any, IO, Self, Tuple

import wx

from quivilib.util import rescale_by_size_factor


class ImageHandler(Protocol):
    """ Interface for a generic image.
    The actual Image class for the appropriate handler (i.e. Freeimage or PIL) will expose a common set of operations.
    """
    @classmethod
    def CreateImage(cls, f:IO[bytes], path:str, delay=False) -> Self:
        """Static constructor. Create a new image object."""
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
    
    width: int
    "The current width of the displayed image"
    height: int
    "The current height of the displayed image"

    img_path: str
    "Path to the image. Intended for debugging only. Not referenced."

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
    def getImg(self) -> Any:
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
