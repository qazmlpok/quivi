from typing import Protocol
import wx


class CanvasLike(Protocol):
    @property
    def width(self) -> int:
        pass

    @property
    def height(self) -> int:
        pass

class CanvasAdapter(CanvasLike):
    def __init__(self, panel: wx.Panel):
        self.panel = panel

    @property
    def width(self) -> int:
        return self.panel.GetSize()[0]

    @property
    def height(self) -> int:
        return self.panel.GetSize()[1]