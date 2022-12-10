

from quivilib.model.settings import Settings
from quivilib.resources import images
from quivilib.control.options import get_fit_choices

import wx
from pubsub import pub as Publisher



ZOOM_FACTOR = 25

(MOVE_LEFT,
 MOVE_RIGHT,
 MOVE_UP,
 MOVE_DOWN) = list(range(4))
 
(MOVE_SMALL,
 MOVE_LARGE,
 MOVE_FULL) = list(range(3))



class CanvasController(object):
    
    #TODO: (1,4) Refactor: all canvas.changed should be sent by the model, but it would
    #      send repeated messages.
    #TODO: (1,3) Improve: messages should only be sent if something has really changed
    
    def __init__(self, name, canvas, view, settings=None):
        self.name = name
        self.canvas = canvas
        self.view = view
        self.settings = settings
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
        self._default_cursor = wx.Cursor(images.cursor_hand.GetImage())
        self._moving_cursor = wx.Cursor(images.cursor_drag.GetImage())
        Publisher.sendMessage(f'{self.name}.cursor.changed', cursor=self._default_cursor)
        
    def on_canvas_painted(self, *, dc, painted_region):
        self.canvas.paint(dc)
        if self.canvas.tiled:
            painted_region.top = 0
            painted_region.left = 0
            painted_region.width = self.view.width
            painted_region.height = self.view.height
        else:
            painted_region.top = self.canvas.top
            painted_region.left = self.canvas.left
            painted_region.width = self.canvas.width
            painted_region.height = self.canvas.height
        
    def on_canvas_resized(self):
        self.canvas.center()
        Publisher.sendMessage(f'{self.name}.changed')
        
    def on_canvas_scrolled(self, *, lines, horizontal=False):
        if horizontal:
            scr = self.view.width
            inc = int(scr * (0.15 / 3) * lines)
            self.canvas.left += (inc)
        else:
            scr = self.view.height
            inc = int(scr * (0.2 / 3) * lines)
            self.canvas.top += (inc)
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
    
    def on_canvas_mouse_event(self, *, button, event):
        if self.name == 'canvas':
            button_name = ('Left', 'Middle', 'Right', 'Aux1', 'Aux2')[button]
            cmd_ide = self.settings.getint('Mouse', f'{button_name}ClickCmd')
            always_drag = self.settings.get('Mouse', 'AlwaysLeftMouseDrag') == '1'
            #Reproduce the old drag behavior (left mouse always drags; run command iff mouse didn't move)
            #if configured. Otherwise, the drag behavior will be a regular command.
            if always_drag and button == 0:
                if event == 0:
                    Publisher.sendMessage(f'{self.name}.cursor.changed', cursor=self._moving_cursor)
                    self._moving_image = True
                elif event == 1:
                    if not self._moved_image:
                        #TODO: Possibly change to "if mouse moved less than x pixels
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
        self.set_zoom_by_fit_type(Settings.FIT_WIDTH)
        
    def zoom_fit_height(self):
        self.set_zoom_by_fit_type(Settings.FIT_HEIGHT)
        
    def set_zoom_by_fit_type(self, fit_type, scr_w = -1, save=False):
        self.canvas.set_zoom_by_fit_type(fit_type, scr_w)
        if save:
            self.settings.set('Options', 'FitType', fit_type)
        Publisher.sendMessage(f'{self.name}.changed')
        
    def move_image(self, direction, typ):
        if direction in (MOVE_RIGHT, MOVE_LEFT):
            scr = self.view.width
        else:
            scr = self.view.height
        if typ == MOVE_LARGE:
            inc = int(scr * 0.8)
        elif typ == MOVE_SMALL:
            inc = int(scr * 0.2)
        else:
            #Adding all these together will guarantee the scroll is always complete
            #Any arbitrary number could theoretically be surpassed if I ever implement infinite scroll.
            inc = self.canvas.width + self.canvas.view.width + self.canvas.height + self.canvas.view.height
        if direction == MOVE_LEFT:
            self.canvas.left += inc
        elif direction == MOVE_RIGHT:
            self.canvas.left -= inc
        elif direction == MOVE_UP:
            self.canvas.top += inc
        elif direction == MOVE_DOWN:
            self.canvas.top -= inc
        Publisher.sendMessage(f'{self.name}.changed')
        
    def rotate_image(self, clockwise):
        self.canvas.rotate(clockwise)
