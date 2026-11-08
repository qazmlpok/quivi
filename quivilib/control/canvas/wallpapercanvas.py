import logging

import wx

from quivilib.control.canvas.basecanvas import BaseCanvasController
from quivilib.interface.canvasadapter import CanvasLike
from quivilib.model.canvas.basecanvas import PaintedRegion
from quivilib.model.canvas.wallpapercanvas import WallpaperCanvas

ZOOM_FACTOR = 25

log = logging.getLogger('control.canvas')


class WallpaperCanvasController(BaseCanvasController):
    def __init__(self, canvas: WallpaperCanvas, view: CanvasLike):
        super().__init__('wpcanvas', view, canvas)
        # Redefine self.canvas to the more-specific type
        self.canvas = canvas

    def on_canvas_painted(self, *, dc: wx.DC, painted_region: PaintedRegion):
        self.canvas.paint(dc)
        if self.canvas.tiled:
            painted_region.top = 0
            painted_region.left = 0
            painted_region.width = self.view_width
            painted_region.height = self.view_height
        else:
            painted_region.top = self.canvas.top
            painted_region.left = self.canvas.left
            painted_region.width = self.canvas.width
            painted_region.height = self.canvas.height

    def on_canvas_mouse_event(self, *, button: int, event: int, x: int, y: int):
        if button == 0 and event == 0:
            self._moving_image = True
        elif button == 0 and event == 1:
            self._moving_image = False
        self._moved_image = False
        self.update_cursor()
