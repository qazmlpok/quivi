import wx
import wx.aui
from pubsub import pub as Publisher

from quivilib import meta
from quivilib.model.canvas import PaintedRegion
from quivilib.model.settings import Settings


class QuiviViewPanel(wx.Panel):
    """The main view panel. This is where the image is displayed"""
    def __init__(self, parent: wx.Window):
        wx.Panel.__init__(self, parent)
        self.SetBackgroundStyle(wx.BG_STYLE_PAINT)

        self.Bind(wx.EVT_PAINT, self.on_panel_paint)
        self.Bind(wx.EVT_MOUSEWHEEL, self.on_mouse_wheel)
        self.Bind(wx.EVT_MOTION, self.on_mouse_motion)
        self._bind_panel_mouse_events()

        Publisher.subscribe(self.on_canvas_changed, 'canvas.changed')
        Publisher.subscribe(self.on_canvas_cursor_changed, 'canvas.cursor.changed')
        Publisher.subscribe(self.on_bg_color_changed, 'settings.loaded')
        Publisher.subscribe(self.on_bg_color_changed, 'settings.changed.Options.CustomBackground')
        Publisher.subscribe(self.on_bg_color_changed, 'settings.changed.Options.CustomBackgroundColor')

    def _bind_panel_mouse_events(self):
        def make_fn(btn_idx: int, evt_idx: int):
            def fn(evt: wx.MouseEvent):
                Publisher.sendMessage('canvas.mouse.event', button=btn_idx, event=evt_idx, x=evt.x, y=evt.y)
                evt.Skip()
            return fn
        for button_idx, button in enumerate(('LEFT', 'MIDDLE', 'RIGHT', 'MOUSE_AUX1', 'MOUSE_AUX2')):
            for event_idx, event in enumerate(('DOWN', 'UP')):
                eid = getattr(wx, f'EVT_{button}_{event}')
                self.Bind(eid, make_fn(button_idx, event_idx))

    @property
    def width(self) -> int:
        return self.GetSize()[0]

    @property
    def height(self) -> int:
        return self.GetSize()[1]

    def on_bg_color_changed(self, *, settings: Settings):
        if settings.get('Options', 'CustomBackground') == '1':
            color = settings.get('Options', 'CustomBackgroundColor').split(',')
            color = wx.Colour(*[int(c) for c in color])
        else:
            color = wx.SystemSettings.GetColour(wx.SYS_COLOUR_APPWORKSPACE)
        self.SetBackgroundColour(color)
        self.Refresh()

    def on_canvas_changed(self):
        self.Refresh(eraseBackground=False)

    def on_canvas_cursor_changed(self, *, cursor: wx.Cursor):
        self.SetCursor(cursor)

    def on_panel_paint(self, event: wx.PaintEvent):
        #In theory it is possible to only update the "dirty" areas but `self.GetUpdateRegion().GetBox()` always gives me (0,0,0,0).
        dc: wx.DC
        if meta.DOUBLE_BUFFERING:
            dc = wx.BufferedPaintDC(self)
            dc.Clear()
        else:
            dc = wx.PaintDC(self)
        #This is required on Linux
        dc.SetBackground(wx.Brush(self.GetBackgroundColour()))
        painted_region = PaintedRegion()
        #The recipient will update the painted_region fields.
        Publisher.sendMessage('canvas.painted', dc=dc, painted_region=painted_region)

        #if meta.DOUBLE_BUFFERING is false, the image is slightly offset and it's possible to scroll the image outside the window on one side.
        #This doesn't happen with double buffering. I have no idea why.
        #The old code for a bug in linux did not work correctly and has no bearing on this issue.
        pass

    def on_mouse_wheel(self, event: wx.MouseEvent):
        lines = event.GetWheelRotation() / event.GetWheelDelta()
        lines *= event.GetLinesPerAction()
        if event.controlDown:
            #Zoom instead of scrolling
            Publisher.sendMessage('canvas.zoom_at', lines=lines, x=event.X, y=event.Y)
        else:
            Publisher.sendMessage('canvas.scrolled', lines=lines, horizontal=event.shiftDown)

    def on_mouse_motion(self, event: wx.MouseEvent):
        Publisher.sendMessage('canvas.mouse.motion', x=event.GetX(), y=event.GetY())
        event.Skip()
