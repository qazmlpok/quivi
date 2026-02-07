from typing import Protocol, Any, IO, Self


class ImageHandler(Protocol):
    """ Interface for a generic image.
    The actual Image class for the appropriate handler (i.e. Freeimage or PIL) will expose a common set of operations.
    """
    @classmethod
    def CreateImage(cls, f:IO[bytes]|None=None, path:str|None=None, img=None, delay=False) -> Self:
        pass
    def delayed_load(self) -> None:
        pass
    def resize(self, width: int, height: int) -> None:
        pass
    def resize_by_factor(self, factor: float) -> None:
        pass
    def rotate(self, clockwise: int) -> None:
        pass
    def rescale(self, width: int, height: int):
        pass
    def paint(self, dc, x: int, y: int) -> None:
        pass
    def copy(self) -> 'ImageHandler':
        pass
    def copy_to_clipboard(self) -> None:
        pass
    def create_thumbnail(self, width: int, height: int, delay: bool):
        pass
    
    width: int
    height: int
    original_width: int
    original_height: int
    #This is an implementation detail so it should probably at least be a function...
    img: Any
    
    @staticmethod
    def extensions() -> list[str]:
        pass

class SecondaryImageHandler(ImageHandler):
    @classmethod
    def CreateWrappedImage(cls, src: ImageHandler | None = None, delay=False) -> ImageHandler:
        pass
