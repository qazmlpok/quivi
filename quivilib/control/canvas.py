

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
 MOVE_LARGE) = list(range(2))
     

     
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
        
    def on_canvas_scrolled(self, *, lines):
        scr = self.view.height
        inc = int(scr * (0.2 / 3) * lines)
        self.canvas.top += (inc)
        Publisher.sendMessage(f'{self.name}.changed')
        
    def on_canvas_mouse_event(self, *, button, event):
        if self.name == 'canvas':
            button_name = ('Left', 'Middle', 'Right')[button]
            cmd_ide = self.settings.getint('Mouse', f'{button_name}ClickCmd')
            #TODO: (2,2) Refactor: change to constant. This is a dummy command ID
            # for "drag image". See settings.py
            if event == 0 and button == 0:
                Publisher.sendMessage(f'{self.name}.cursor.changed', cursor=self._moving_cursor)
                self._moving_image = True
            if event == 1 and (not self._moved_image or button != 0):
                Publisher.sendMessage('command.execute', ide=cmd_ide)
            if event == 1 and button == 0:
                Publisher.sendMessage(f'{self.name}.cursor.changed', cursor=self._default_cursor)
                self._moving_image = False
        else:
            #Not the main canvas (e.g. wallpaper dialog canvas)
            if button == 0 and event == 0:
                Publisher.sendMessage(f'{self.name}.cursor.changed', cursor=self._moving_cursor)
                self._moving_image = True
            elif button == 0 and event == 1:
                Publisher.sendMessage(f'{self.name}.cursor.changed', cursor=self._default_cursor)
                self._moving_image = False
        self._moved_image = False


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

    def _zoom(self, zoom_in):
        zoom = 1 + ZOOM_FACTOR / 100.0
        zoom = zoom if zoom_in else 1.0 / zoom
        self.canvas.zoom *= zoom
        
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
        inc = int(scr * (0.8 if typ == MOVE_LARGE else 0.2))
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
