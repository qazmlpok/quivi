from typing import Protocol

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