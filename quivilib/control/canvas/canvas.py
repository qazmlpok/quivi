import logging
import time
from typing import IO

import wx
from pubsub import pub as Publisher

from quivilib import meta
from quivilib.control.cache import ImageCacheLoadRequest, ImageCacheLoaded
from quivilib.control.canvas.basecanvas import BaseCanvasController
from quivilib.interface.canvasadapter import CanvasLike
from quivilib.model import image
from quivilib.model.canvas.basecanvas import PaintedRegion
from quivilib.model.canvas.canvas import Canvas
from quivilib.model.commandenum import FitSettings
from quivilib.model.settings import Settings
from quivilib.util import DebugTimer

ZOOM_FACTOR = 25

log = logging.getLogger('control.canvas')


class CanvasController(BaseCanvasController):
    #TODO: (1,4) Refactor: all canvas.changed should be sent by the model, but it would
    #      send repeated messages.
    #TODO: (1,3) Improve: messages should only be sent if something has really changed
    
    def __init__(self, view: CanvasLike, settings: Settings, oldcontroller: CanvasController | None = None):
        self.settings: Settings = settings
        #PEP 823. Using 'and' gives wrong type hint.
        oldcanvas = None
        if oldcontroller is not None:
            oldcanvas = oldcontroller.canvas
        canvas = Canvas(settings, oldcanvas)
        super().__init__('canvas', view, canvas=canvas)

        self.pending_request: ImageCacheLoadRequest|None = None
        if oldcontroller is not None:
            self.pending_request = oldcontroller.pending_request
        Publisher.subscribe(self.on_request_open_image, f'{self.name}.load.img')
        Publisher.subscribe(self.on_cache_image_loaded, 'cache.image_loaded')
        Publisher.subscribe(self.on_cache_image_load_error, 'cache.image_load_error')
        Publisher.subscribe(self.on_timer, 'timer.pulse')

    def on_canvas_painted(self, *, dc: wx.DC, painted_region: PaintedRegion):
        # Reminder - this is updating the painted_region object. The caller will use these values.
        # pubsub isn't supposed to be used this way.
        self.canvas.paint(dc)
        painted_region.top = self.canvas.top
        painted_region.left = self.canvas.left
        painted_region.width = self.canvas.width
        painted_region.height = self.canvas.height

    def on_canvas_mouse_event(self, *, button: int, event: int, x: int, y: int):
        button_name = ('Left', 'Middle', 'Right', 'Aux1', 'Aux2')[button]
        cmd_ide = self.settings.getint('Mouse', f'{button_name}ClickCmd')
        always_drag = self.settings.get('Mouse', 'AlwaysLeftMouseDrag') == '1'
        drag_threshold = self.settings.getint('Mouse', 'DragThreshold')
        # Reproduce the old drag behavior (left mouse always drags; run command iff mouse didn't move) if configured.
        # Otherwise, the drag behavior will be a regular command.
        if always_drag and button == 0:
            if event == 0:
                self._moving_image = True
                self._orig_mouse_pos = (x, y)
            elif event == 1:
                # If always dragging but the mouse hasn't moved (within the configured delta), execute the click event anyway
                xdiff = self._orig_mouse_pos[0] - x
                ydiff = self._orig_mouse_pos[1] - y
                if not self._moved_image or (xdiff ** 2 + ydiff ** 2 < drag_threshold ** 2):
                    Publisher.sendMessage('command.execute', ide=cmd_ide)
                self._moving_image = False
        elif event == 0:
            Publisher.sendMessage('command.down_execute', ide=cmd_ide)
        elif event == 1:
            Publisher.sendMessage('command.execute', ide=cmd_ide)
        self._moved_image = False
        self.update_cursor()

    def on_canvas_mouse_motion(self, *, x: int, y: int):
        super().on_canvas_mouse_motion(x=x, y=y)
        self._last_cursor_move = time.time()
        self.update_cursor()

    def get_rtl_setting(self):
        return self.settings.getboolean('Options', 'UseRightToLeft')

    def on_timer(self):
        # Generic timer that is called every second. Use it to avoid needing an EvtHandler obj.
        self.update_cursor()

    def update_cursor(self):
        ts = time.time()
        setting = self.settings.getint('Mouse', 'HideMouseDuration')
        if not self.has_image():
            cursor = wx.NullCursor
        elif self._moving_image:
            cursor = self._moving_cursor
        elif self._last_cursor_move is not None and 0 < setting < ts - self._last_cursor_move:
            cursor = self._blank_cursor
        else:
            cursor = self._default_cursor

        #SetCursor appears to take a trivial amount of time, but this is called with every touch of the mouse.
        if cursor is not self._current_cursor:
            Publisher.sendMessage(f'{self.name}.cursor.changed', cursor=cursor)
            self._current_cursor = cursor

    # Open/close image
    def close_img(self):
        self.canvas.close_img()

    # Image loading (moved from file list)
    def on_request_open_image(self, *, container, item, preload=False):
        if meta.CACHE_ENABLED:
            request = ImageCacheLoadRequest(container, item)
            if not preload:
                self.pending_request = request
                Publisher.sendMessage('cache.clear_pending', request=request)
                Publisher.sendMessage('container.image.loading', item=item)
            Publisher.sendMessage('cache.load_image', request=request, preload=preload)
            log.debug("canvas: cache requested")
            if not preload and self.pending_request is not None:
                # Small hack; if the image is cached on_cache_image_loaded will be called immediately.
                Publisher.sendMessage('busy', busy=True)
        else:
            Publisher.sendMessage('busy', busy=True)
            path = item.path
            item_index = container.items.index(item)
            f: IO[bytes] = container.open_image(item_index)
            # can't use "with" because not every file-like object used here supports it
            try:
                with DebugTimer(path.name):
                    img = image.open_img(f, path)
                    self.canvas.load_img(img)
            finally:
                f.close()
            Publisher.sendMessage('busy', busy=False)
            Publisher.sendMessage('container.image.opened', item=item)

    def on_cache_image_loaded(self, *, request: ImageCacheLoaded):
        if request == self.pending_request:
            self.pending_request = None
            self.canvas.load_img(request.img)
            Publisher.sendMessage('busy', busy=False)
            item = request.item
            Publisher.sendMessage('container.image.opened', item=item)
            # First image load needs to update the cursor
            self.update_cursor()

    def on_cache_image_load_error(self, *, request: ImageCacheLoadRequest, exception, tb):
        if request == self.pending_request:
            Publisher.sendMessage('busy', busy=False)
            Publisher.sendMessage('error', exception=exception, tb=tb)
            self.pending_request = None

    #Zoom commands
    def zoom_reset(self):
        self.canvas.zoom_reset()
        Publisher.sendMessage(f'{self.name}.changed')

    def zoom_fit_width(self):
        self.set_zoom_by_fit_type(FitSettings.FitType.WIDTH_IF_LARGER)

    def zoom_fit_height(self):
        self.set_zoom_by_fit_type(FitSettings.FitType.HEIGHT_IF_LARGER)

    def zoom_fit_both(self):
        self.set_zoom_by_fit_type(FitSettings.FitType.WINDOW_IF_LARGER)

    def set_zoom_by_fit_type(self, fit_type, scr_w=-1, save=False):
        #Override to allow saving
        self.canvas.set_zoom_by_fit_type(fit_type, scr_w)
        if save:
            self.settings.set('Options', 'FitType', fit_type)
        Publisher.sendMessage(f'{self.name}.changed')

    def set_zoom_by_current_fit(self):
        fit_type = self.settings.get('Options', 'FitType')
        fit_type = FitSettings.get_fittype(fit_type)
        self.set_zoom_by_fit_type(fit_type)
        Publisher.sendMessage(f'{self.name}.changed')

    def print_canvas_info(self):
        """Debug method - just dump a lot of canvas stuff to console."""
        if not __debug__:
            return
        if self.canvas.img is None:
            print("No image.")
            return
        halfw = self.view_width // 2
        halfh = self.view_height // 2
        print(f"Width x Height: {self.canvas.width} x {self.canvas.height}  ({self.canvas.img.base_width} x {self.canvas.img.base_height})")
        print(f"Left: {self.canvas.left} ({self.canvas.left/self.canvas.width*100:0.2f}%)")
        print(f"Top: {self.canvas.top} ({self.canvas.top/self.canvas.height*100:0.2f}%)")
        print(f"Zoom: {self.canvas.zoom * 100:0.2f}%")
        print(f"Left Center: {self.canvas.left - halfw} ({(self.canvas.left - halfw) / self.canvas.width * 100:0.2f}%)")
        print(f"Top Center: {self.canvas.top - halfh} ({(self.canvas.top - halfh) / self.canvas.height * 100:0.2f}%)")
        print()
        print(f"View: {self.view_width} x {self.view_height}")
        print(f"Class: {type(self)}  -- Canvas class: {type(self.canvas)}")
        print()
        print()

    def scuttle(self):
        #Unsubscribe from events
        Publisher.unsubscribe(self.on_request_open_image, f'{self.name}.load.img')
        Publisher.unsubscribe(self.on_cache_image_loaded, 'cache.image_loaded')
        Publisher.unsubscribe(self.on_cache_image_load_error, 'cache.image_load_error')
        Publisher.unsubscribe(self.on_timer, 'timer.pulse')
        #Unsubscribe parent events
        Publisher.unsubscribe(self.on_canvas_painted, f'{self.name}.painted')
        Publisher.unsubscribe(self.on_canvas_resized, f'{self.name}.resized')
        Publisher.unsubscribe(self.on_canvas_scrolled, f'{self.name}.scrolled')
        Publisher.unsubscribe(self.on_canvas_zoom_point, f'{self.name}.zoom_at')
        Publisher.unsubscribe(self.on_canvas_mouse_event, f'{self.name}.mouse.event')
        Publisher.unsubscribe(self.on_canvas_mouse_motion, f'{self.name}.mouse.motion')
        Publisher.unsubscribe(self.on_program_closed, 'program.closed')
        # Trash the canvas too
        self.canvas.scuttle()
        # Set these to None so any attempt to use the old object triggers a bunch of errors.
        proplist = ['name', 'canvas', 'view', '_current_cursor', 'on_request_open_image', 'on_cache_image_loaded']
        for n in proplist:
            setattr(self, n, None)
