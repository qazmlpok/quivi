import logging
import wx
from pubsub import pub as Publisher

from quivilib import meta
from quivilib.interface.canvasadapter import CanvasLike
from quivilib.model.commandenum import MovementType, FitSettings
from quivilib.model.canvas import Canvas, PaintedRegion, WallpaperCanvas
from quivilib.model.settings import Settings
from quivilib.resources import images
from quivilib.util import DebugTimer
from quivilib.control.cache import ImageCacheLoadRequest, ImageCacheLoaded

ZOOM_FACTOR = 25

log = logging.getLogger('control.canvas')

class CanvasController(object):
    #TODO: (1,4) Refactor: all canvas.changed should be sent by the model, but it would
    #      send repeated messages.
    #TODO: (1,3) Improve: messages should only be sent if something has really changed
    
    def __init__(self, name, view: CanvasLike, canvas: Canvas = None, settings: Settings = None):
        self.name = name
        if canvas is None:
            self.canvas = Canvas('canvas', settings)
        else:
            #Hack for the wallpaper. I don't like this but don't feel like trying to find something better.
            self.canvas = canvas
        self.canvas.set_view(view)
        self.view = view
        self.settings = settings
        self.pending_request = None
        Publisher.subscribe(self.on_request_open_image, f'{self.name}.load.img')
        Publisher.subscribe(self.on_cache_image_loaded, 'cache.image_loaded')
        Publisher.subscribe(self.on_cache_image_load_error, 'cache.image_load_error')
        Publisher.subscribe(self.on_canvas_painted, f'{self.name}.painted')
        Publisher.subscribe(self.on_canvas_resized, f'{self.name}.resized')
        Publisher.subscribe(self.on_canvas_scrolled, f'{self.name}.scrolled')
        Publisher.subscribe(self.on_canvas_zoom_point, f'{self.name}.zoom_at')
        Publisher.subscribe(self.on_canvas_mouse_event, f'{self.name}.mouse.event')
        Publisher.subscribe(self.on_canvas_mouse_motion, f'{self.name}.mouse.motion')
        #Indicates that the user is moving the image
        self._moving_image = False
        #Indicates that the user has moved the image significantly 
        self._moved_image = False
        self._old_mouse_pos = (-1, -1)
        self._orig_mouse_pos = (-1, -1)
        self._default_cursor = wx.Cursor(images.cursor_hand.GetImage())
        self._moving_cursor = wx.Cursor(images.cursor_drag.GetImage())
        Publisher.sendMessage(f'{self.name}.cursor.changed', cursor=self._default_cursor)

    #Passthru methods to the model Canvas
    def copy_to_clipboard(self):
        return self.canvas.copy_to_clipboard()
    def has_image(self) -> bool:
        return self.canvas.has_image()
    def get_img(self):
        return self.canvas.img

    def close_img(self):
        self.canvas.close_img()

    #Image loading (moved from file list)
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
                #Small hack; if the image is cached on_cache_image_loaded will be called immediately.
                Publisher.sendMessage('busy', busy=True)
        else:
            Publisher.sendMessage('busy', busy=True)
            path = item.path
            item_index = container.items.index(item)
            f = container.open_image(item_index)
            #can't use "with" because not every file-like object used here supports it
            try:
                with DebugTimer(path.name):
                    img = self.canvas.load(f, path)
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
    def on_cache_image_load_error(self, *, request: ImageCacheLoadRequest, exception, tb):
        if request == self.pending_request:
            Publisher.sendMessage('busy', busy=False)
            Publisher.sendMessage('error', exception=exception, tb=tb)
            #Wasn't being done before. Kinda odd.
            self.pending_request = None

    #Drawing
    def on_canvas_painted(self, *, dc: wx.DC, painted_region: PaintedRegion):
        self.canvas.paint(dc)
        painted_region.top = self.canvas.top
        painted_region.left = self.canvas.left
        painted_region.width = self.canvas.width
        painted_region.height = self.canvas.height
        
    def on_canvas_resized(self):
        self.canvas.center()
        Publisher.sendMessage(f'{self.name}.changed')
        
    def on_canvas_scrolled(self, *, lines, horizontal=False):
        if horizontal:
            rtl = self.settings.getboolean('Options', 'UseRightToLeft')
            scr = self.view.width
            inc = int(scr * (0.15 / 3) * lines)
            #Invert direction if in right-to-left mode. Mousewheel down should always be to the "end" of the image.
            self.canvas.scroll_hori(inc, rtl)
        else:
            scr = self.view.height
            inc = int(scr * (0.2 / 3) * lines)
            self.canvas.scroll_vert(inc)
        Publisher.sendMessage(f'{self.name}.changed')
    
    def on_canvas_zoom_point(self, *, lines, x, y):
        """ Zoom in or out. Unlike the keyboard command, this will shift the canvas as well
        in order to zoom in/out specifically at the mouse's position.
        """
        old_top, old_left =  self.canvas.top, self.canvas.left
        old_w, old_h = self.canvas.width, self.canvas.height
        scale = ZOOM_FACTOR * (abs(lines) / 3)
        self._zoom_to_point(lines > 0, x, y, zoom_scale=scale)
        Publisher.sendMessage(f'{self.name}.changed')
    
    def on_canvas_mouse_event(self, *, button, event, x, y):
        if self.name == 'canvas':
            button_name = ('Left', 'Middle', 'Right', 'Aux1', 'Aux2')[button]
            cmd_ide = self.settings.getint('Mouse', f'{button_name}ClickCmd')
            always_drag = self.settings.get('Mouse', 'AlwaysLeftMouseDrag') == '1'
            drag_threshold = self.settings.getint('Mouse', 'DragThreshold')
            #Reproduce the old drag behavior (left mouse always drags; run command iff mouse didn't move)
            #if configured. Otherwise, the drag behavior will be a regular command.
            if always_drag and button == 0:
                if event == 0:
                    Publisher.sendMessage(f'{self.name}.cursor.changed', cursor=self._moving_cursor)
                    self._moving_image = True
                    self._orig_mouse_pos = (x, y)
                elif event == 1:
                    #If always dragging but the mouse hasn't moved (within the configured delta), execute the click event anyway
                    xdiff = self._orig_mouse_pos[0] - x
                    ydiff = self._orig_mouse_pos[1] - y
                    if not self._moved_image or (xdiff**2 + ydiff**2 < drag_threshold**2):
                        Publisher.sendMessage('command.execute', ide=cmd_ide)
                    Publisher.sendMessage(f'{self.name}.cursor.changed', cursor=self._default_cursor)
                    self._moving_image = False
            elif event == 0:
                Publisher.sendMessage('command.down_execute', ide=cmd_ide)
            elif event == 1:
                Publisher.sendMessage('command.execute', ide=cmd_ide)
        else:
            #Not the main canvas (e.g. wallpaper dialog canvas)
            if button == 0 and event == 0:
                Publisher.sendMessage(f'{self.name}.cursor.changed', cursor=self._moving_cursor)
                self._moving_image = True
            elif button == 0 and event == 1:
                Publisher.sendMessage(f'{self.name}.cursor.changed', cursor=self._default_cursor)
                self._moving_image = False
        self._moved_image = False

    def image_drag_start(self):
        Publisher.sendMessage(f'{self.name}.cursor.changed', cursor=self._moving_cursor)
        self._moving_image = True
    def image_drag_end(self):
        Publisher.sendMessage(f'{self.name}.cursor.changed', cursor=self._default_cursor)
        self._moving_image = False

    def on_canvas_mouse_motion(self, *, x, y):
        old_x, old_y = self._old_mouse_pos
        canvas = self.canvas
        if old_x != -1 and self._moving_image:
            dx, dy = x - old_x, y - old_y
            self._moved_image = True
            scale_x = canvas.width / float(self.view.width)
            scale_y = canvas.height / float(self.view.height)
            scale_x = 1 if scale_x < 1 else scale_x
            scale_y = 1 if scale_y < 1 else scale_y
            canvas.left += int(dx * scale_x)
            canvas.top += int(dy * scale_y)
            Publisher.sendMessage(f'{self.name}.changed')
        self._old_mouse_pos = x, y

    def _zoom(self, zoom_in, zoom_scale=ZOOM_FACTOR):
        zoom = 1 + zoom_scale / 100.0
        zoom = zoom if zoom_in else 1.0 / zoom
        #(Calls the setter _set_zoom)
        self.canvas.zoom *= zoom
    def _zoom_to_point(self, zoom_in, x, y, zoom_scale=ZOOM_FACTOR):
        zoom = 1 + zoom_scale / 100.0
        zoom = zoom if zoom_in else 1.0 / zoom
        self.canvas.zoom_to_point(self.canvas.zoom * zoom, x, y)

    def zoom_in(self):
        self._zoom(True)
        Publisher.sendMessage(f'{self.name}.changed')
        
    def zoom_out(self):
        self._zoom(False)
        Publisher.sendMessage(f'{self.name}.changed')
        
    def zoom_reset(self):
        self.canvas.zoom = 1
        Publisher.sendMessage(f'{self.name}.changed')
        
    def zoom_fit_width(self):
        self.set_zoom_by_fit_type(FitSettings.FIT_WIDTH)
        
    def zoom_fit_height(self):
        self.set_zoom_by_fit_type(FitSettings.FIT_HEIGHT)
        
    def set_zoom_by_fit_type(self, fit_type, scr_w = -1, save=False):
        self.canvas.set_zoom_by_fit_type(fit_type, scr_w)
        if save:
            self.settings.set('Options', 'FitType', fit_type)
        Publisher.sendMessage(f'{self.name}.changed')
    
    def set_zoom_by_current_fit(self):
        fit_type = self.settings.getint('Options', 'FitType')
        self.set_zoom_by_fit_type(fit_type)
        Publisher.sendMessage(f'{self.name}.changed')
        
    def move_image(self, direction, typ):
        if direction & MovementType.MOVE_HORI:
            scr = self.view.width
            scr_fn = self.canvas.scroll_hori
        else:
            scr = self.view.height
            scr_fn = self.canvas.scroll_vert
        scr_rev = direction & MovementType.MOVE_NEG
        if typ == MovementType.MOVETYPE_LARGE:
            inc = int(scr * 0.8)
        elif typ == MovementType.MOVETYPE_SMALL:
            inc = int(scr * 0.2)
        else:
            #Adding all these together will guarantee the scroll is always complete
            #Any arbitrary number could theoretically be surpassed if I ever implement infinite scroll.
            inc = self.canvas.width + self.canvas.view.width + self.canvas.height + self.canvas.view.height
        
        #Call the appropriate canvas scroll_x function
        #Note - scroll up/down will scroll left/right if at the image border. I don't know if this is appropriate behavior for this source of scrolling.
        scr_fn(inc, scr_rev)
        Publisher.sendMessage(f'{self.name}.changed')
        
    def rotate_image(self, clockwise):
        self.canvas.rotate(clockwise)

class WallpaperCanvasController(CanvasController):
    def __init__(self, name, canvas: WallpaperCanvas, view, settings: Settings = None):
        #It should be possible to remove some of the event subscriptions
        #but that would require a base class instead of direct inheritence.
        super().__init__(name, view, canvas=canvas)
    def on_canvas_painted(self, *, dc, painted_region):
        self.canvas.paint(dc)
        if self.canvas.tiled:
            painted_region.top = 0
            painted_region.left = 0
            painted_region.width = self.view.width
            painted_region.height = self.view.height
        else:
            super().on_canvas_painted(dc=dc, painted_region=painted_region)
