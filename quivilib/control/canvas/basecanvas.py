import logging

import wx
from pubsub import pub as Publisher

from quivilib.interface.canvasadapter import CanvasLike
from quivilib.model.canvas.basecanvas import PaintedRegion, BaseCanvas
from quivilib.model.commandenum import MovementType, MovementSize
from quivilib.resources import images

ZOOM_FACTOR = 25

log = logging.getLogger('control.canvas')


class BaseCanvasController(object):
    def __init__(self, name: str, view: CanvasLike, canvas: BaseCanvas):
        self.name = name
        self.canvas = canvas
        self.canvas.set_view(view)
        self.view = view
        Publisher.subscribe(self.on_canvas_painted, f'{self.name}.painted')
        Publisher.subscribe(self.on_canvas_resized, f'{self.name}.resized')
        Publisher.subscribe(self.on_canvas_scrolled, f'{self.name}.scrolled')
        Publisher.subscribe(self.on_canvas_zoom_point, f'{self.name}.zoom_at')
        Publisher.subscribe(self.on_canvas_mouse_event, f'{self.name}.mouse.event')
        Publisher.subscribe(self.on_canvas_mouse_motion, f'{self.name}.mouse.motion')
        Publisher.subscribe(self.on_program_closed, 'program.closed')
        # Indicates that the user is moving the image
        self._moving_image: bool = False
        # Indicates that the user has moved the image significantly
        self._moved_image: bool = False
        self._old_mouse_pos: tuple[int, int] = (-1, -1)
        self._orig_mouse_pos: tuple[int, int] = (-1, -1)
        self._last_cursor_move: float|None = None
        self._default_cursor = wx.Cursor(images.cursor_hand.GetImage())     # (Open Hand)
        self._moving_cursor = wx.Cursor(images.cursor_drag.GetImage())      # (Closed Hand)
        self._blank_cursor = wx.Cursor(wx.CURSOR_BLANK)                     # (Invisible)
        self._current_cursor = None
        self.update_cursor()

    @property
    def view_width(self):
        """Returns the width of the current display area (i.e. depends on the application window size)"""
        return self.view.width

    @property
    def view_height(self):
        """Returns the height of the current display area (i.e. depends on the application window size)"""
        return self.view.height

    def update_cursor(self):
        """Update the mouse cursor depending on state.
        If there is no image, use the OS default cursor.
        If actively dragging the current image, use a closed hand.
        If not dragging the image, use an open hand.
        If the mouse hasn't moved in a while, hide the cursor. This is a configuration setting and only applies to the main canvas
        """
        if not self.has_image():
            cursor = wx.NullCursor
        elif self._moving_image:
            cursor = self._moving_cursor
        else:
            cursor = self._default_cursor

        #SetCursor appears to take a trivial amount of time, but this is called with every touch of the mouse.
        if cursor is not self._current_cursor:
            Publisher.sendMessage(f'{self.name}.cursor.changed', cursor=cursor)
            self._current_cursor = cursor

    def on_canvas_painted(self, *, dc: wx.DC, painted_region: PaintedRegion):
        raise NotImplementedError("Implement in subclass")

    def on_canvas_mouse_event(self, *, button: int, event: int, x: int, y: int):
        raise NotImplementedError("Implement in subclass")

    def get_rtl_setting(self):
        """Hack for wallpaper, which doesn't have settings"""
        return False

    # Passthru methods to the model Canvas
    def copy_to_clipboard(self):
        return self.canvas.copy_to_clipboard()

    def has_image(self) -> bool:
        return self.canvas.has_image()

    def get_img(self):
        return self.canvas.img

    # Drawing
    def on_canvas_resized(self):
        self.canvas.center()
        Publisher.sendMessage(f'{self.name}.changed')

    def on_canvas_scrolled(self, *, lines, horizontal=False):
        if horizontal:
            rtl = self.get_rtl_setting()
            scr = self.view_width
            inc = int(scr * (0.15 / 3) * lines)
            # Invert direction if in right-to-left mode. Mousewheel down should always be to the "end" of the image.
            self.canvas.scroll_hori(inc, rtl)
        else:
            scr = self.view_height
            inc = int(scr * (0.2 / 3) * lines)
            self.canvas.scroll_vert(inc)
        Publisher.sendMessage(f'{self.name}.changed')

    def on_canvas_zoom_point(self, *, lines: float, x: int, y: int):
        """ Zoom in or out. Unlike the keyboard command, this will shift the canvas as well
        in order to zoom in/out specifically at the mouse's position.
        """
        scale = ZOOM_FACTOR * (abs(lines) / 3)
        self._zoom_to_point(lines > 0, x, y, zoom_scale=scale)
        Publisher.sendMessage(f'{self.name}.changed')

    def image_drag_start(self):
        self._moving_image = True
        self.update_cursor()

    def image_drag_end(self):
        self._moving_image = False
        self.update_cursor()

    def on_canvas_mouse_motion(self, *, x: int, y: int):
        old_x, old_y = self._old_mouse_pos
        canvas = self.canvas
        if old_x != -1 and self._moving_image:
            dx, dy = x - old_x, y - old_y
            self._moved_image = True
            canvas.left += int(dx)
            canvas.top += int(dy)
            Publisher.sendMessage(f'{self.name}.changed')
        self._old_mouse_pos = x, y

    def _zoom(self, zoom_in, zoom_scale=ZOOM_FACTOR):
        zoom = 1 + zoom_scale / 100.0
        zoom = zoom if zoom_in else 1.0 / zoom
        # (Calls the setter _set_zoom)
        self.canvas.zoom *= zoom

    def _zoom_to_point(self, zoom_in, x: int, y: int, zoom_scale: float=ZOOM_FACTOR):
        zoom = 1 + zoom_scale / 100.0
        zoom = zoom if zoom_in else 1.0 / zoom
        self.canvas.zoom_to_point(self.canvas.zoom * zoom, x, y)

    def zoom_in(self):
        self._zoom(True)
        Publisher.sendMessage(f'{self.name}.changed')

    def zoom_out(self):
        self._zoom(False)
        Publisher.sendMessage(f'{self.name}.changed')

    def set_zoom_by_fit_type(self, fit_type, scr_w=-1):
        #Override to allow saving
        self.canvas.set_zoom_by_fit_type(fit_type, scr_w)
        Publisher.sendMessage(f'{self.name}.changed')

    def move_image(self, direction: MovementType, typ: MovementSize):
        if direction & MovementType.MOVE_HORI:
            scr = self.view_width
            scr_fn = self.canvas.scroll_hori
        else:
            scr = self.view_height
            scr_fn = self.canvas.scroll_vert
        scr_rev = direction & MovementType.MOVE_NEG
        if typ == MovementSize.MOVETYPE_LARGE:
            inc = int(scr * 0.8)
        elif typ == MovementSize.MOVETYPE_SMALL:
            inc = int(scr * 0.2)
        else:
            # Adding all these together will guarantee the scroll is always complete
            # Any arbitrary number could theoretically be surpassed if I ever implement infinite scroll.
            inc = self.canvas.width + self.canvas.view.width + self.canvas.height + self.canvas.view.height

        # Call the appropriate canvas scroll_x function
        # Note - scroll up/down will scroll left/right if at the image border. I don't know if this is appropriate behavior for this source of scrolling.
        scr_fn(inc, scr_rev)
        Publisher.sendMessage(f'{self.name}.changed')

    def rotate_image(self, clockwise: int):
        self.canvas.rotate(clockwise)

    def on_program_closed(self, *, settings_lst=None):
        if self.canvas is not None:
            self.canvas.shutdown_received()
