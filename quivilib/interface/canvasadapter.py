from typing import Protocol
import wx


class CanvasLike(Protocol):
    """Something that resembles a real Canvas.
    Models shouldn't know about the view, but the canvas needs the physical dimensions of the display for some actions.
    The CanvasAdapater (and this interface) is used to work around this.
    """
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