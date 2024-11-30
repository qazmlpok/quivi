from typing import Protocol, TypeVar

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
    def copy(self) -> 'ImageHandler':
        pass
    def copy_to_clipboard(self) -> None:
        pass
    def create_thumbnail(self, width: int, height: int, delay: bool):
        pass
