from typing import Protocol, TypeVar

class ImageWrapper(Protocol):
    def allocate(cls: type['ImageWrapper'], width, height, bpp, red_mask=0, green_mask=0, blue_mask=0) -> 'ImageWrapper':
        pass
    def maybeConvert32bit(self: 'ImageWrapper') -> 'ImageWrapper':
        pass
    def convert_to_raw_bits(self, width_bytes=None) -> bytearray:
        pass
    def rescale(self: 'ImageWrapper', width: int, height: int) -> 'ImageWrapper':
        pass
    def fill(self, color) -> None:
        pass
    def paste(self, src, left: int, top: int, alpha: int = 256) -> None:
        pass
    def copy_region(self: 'ImageWrapper', left: int, top: int, right: int, bottom: int) -> 'ImageWrapper':
        pass
    def save_bitmap(self, path) -> None:
        pass
    def save(self, path) -> None:
        pass

class ImageHandler(Protocol):
    def delayed_load(self) -> None:
        pass
    def resize(self, width: int, height: int) -> None:
        pass
    def resize_by_factor(self, factor: float) -> None:
        pass
    def rotate(self, clockwise: int) -> None:
        pass
    def paint(self, dc, x: int, y: int) -> None:
        pass
    def copy(self) -> ImageWrapper:
        pass
    def copy_to_clipboard(self) -> None:
        pass
    def create_thumbnail(self, width: int, height: int, delay: bool):
        pass
