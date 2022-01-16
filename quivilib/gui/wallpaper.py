

from quivilib.i18n import _
from quivilib import util

import wx
import wx.lib.colourselect as csel
from pubsub import pub as Publisher

#TODO: (1,3) Refactor: the whole preview_panel and the main window's panel can be
#      refactored into a single class


class WallpaperDialog(wx.Dialog):
    
    def __init__(self, parent, choices, background_color):
        # begin wxGlade: WallpaperDialog.__init__
        wx.Dialog.__init__(self, parent=parent)
        
        self.bmp = None
        self.tiled = False
        color = background_color
        
        self.preview_panel = wx.Panel(self)
        self.position_radio = wx.RadioBox(self, -1, _("&Position"), choices=choices, majorDimension=0, style=wx.RA_SPECIFY_ROWS)
        self.ok_button = wx.Button(self, wx.ID_OK, _("&Set wallpaper"))
        self.cancel_button = wx.Button(self, wx.ID_CANCEL, _("&Cancel"))
        self.zoom_text_label = wx.StaticText(self, -1, _("Zoom:"), style=wx.ALIGN_RIGHT)
        self.zoom_label = wx.StaticText(self, -1, '00100.00%')
        self.zoom_in_button = wx.Button(self, -1, '+', style=wx.BU_EXACTFIT)
        self.zoom_out_button = wx.Button(self, -1, '-', style=wx.BU_EXACTFIT)
        self.color_text_label = wx.StaticText(self, -1, _("&Color:"), style=wx.ALIGN_RIGHT)
        self.color_button = csel.ColourSelect(self, -1, "", color)

        self.__set_properties()
        self.__do_layout()

        self.Bind(wx.EVT_BUTTON, self.on_set_wallpaper, self.ok_button)
        self.Bind(wx.EVT_BUTTON, self.on_cancel, self.cancel_button)
        self.Bind(wx.EVT_BUTTON, self.on_zoom_in, self.zoom_in_button)
        self.Bind(wx.EVT_BUTTON, self.on_zoom_out, self.zoom_out_button)
        self.Bind(wx.EVT_RADIOBOX, self.on_selection_changed, self.position_radio)
        self.preview_panel.Bind(wx.EVT_PAINT, self.on_screen_panel_paint)
        self.preview_panel.Bind(wx.EVT_MOUSEWHEEL, self.on_mouse_wheel)
        self.preview_panel.Bind(wx.EVT_LEFT_DOWN, self.on_mouse_left_down)
        self.preview_panel.Bind(wx.EVT_LEFT_UP, self.on_mouse_left_up)
        self.preview_panel.Bind(wx.EVT_MOTION, self.on_mouse_motion)
        self.color_button.Bind(csel.EVT_COLOURSELECT, self.on_color_select)
        Publisher.subscribe(self.on_preview_changed, 'wallpaper.preview_changed')
        Publisher.subscribe(self.on_canvas_changed, 'wpcanvas.changed')
        Publisher.subscribe(self.on_canvas_cursor_changed, 'wpcanvas.cursor.changed')
        Publisher.subscribe(self.on_canvas_zoom_changed, 'wpcanvas.zoom.changed')
        
        Publisher.sendMessage('wallpaper.dialog_opened', dialog=self)
        
        Publisher.sendMessage('wallpaper.preview_position_changed',
                                pos_idx=self.position_radio.GetSelection())
        
        self.preview_panel.SetBackgroundStyle(wx.BG_STYLE_COLOUR)
        self.preview_panel.SetBackgroundColour(color)
        # end wxGlade

    def __set_properties(self):
        # begin wxGlade: WallpaperDialog.__set_properties
        self.SetTitle(_("Set as wallpaper"))
        screen = wx.Display(0)
        screen_width = screen.GetGeometry().width
        screen_height = screen.GetGeometry().height
        preview_panel_size = (int(screen_width * 200.0 / screen_height), 200) 
        self.preview_panel.SetMinSize(preview_panel_size)
        self.preview_panel.SetMaxSize(preview_panel_size)
        self.position_radio.SetSelection(0)
        self.ok_button.SetDefault()
        self.zoom_label.SetMinSize(self.zoom_label.GetTextExtent('99999.99%'))
        # end wxGlade
        self.adjust_factor = screen_width / float(preview_panel_size[0])

    def __do_layout(self):
        # begin wxGlade: WallpaperDialog.__do_layout
        grid_sizer_3 = wx.FlexGridSizer(rows=6, cols=3, vgap=5, hgap=5)
        btnsizer = wx.StdDialogButtonSizer()
        sizer_1 = wx.BoxSizer(wx.HORIZONTAL)
        grid_sizer_3.Add((5, 5), 0, 0, 0)
        grid_sizer_3.Add((5, 5), 0, 0, 0)
        grid_sizer_3.Add((5, 5), 0, 0, 0)
        grid_sizer_3.Add((5, 5), 0, 0, 0)
        grid_sizer_3.Add(self.preview_panel, 1, wx.EXPAND, 0)
        grid_sizer_3.Add((5, 5), 0, 0, 0)
        grid_sizer_3.Add((5, 5), 0, 0, 0)
        sizer_1.Add(self.zoom_text_label, 0, wx.ALIGN_CENTER_VERTICAL, 0)
        sizer_1.Add((10, 20), 0, 0, 0)
        sizer_1.Add(self.zoom_label, 0, wx.ALIGN_CENTER_VERTICAL, 0)
        sizer_1.Add((10, 20), 0, 0, 0)
        sizer_1.Add(self.zoom_in_button, 0, 0, 0)
        sizer_1.Add(self.zoom_out_button, 0, 0, 0)
        sizer_1.Add((30, 20), 0, wx.EXPAND, 0)
        sizer_1.Add(self.color_text_label, 0, wx.ALIGN_CENTER_VERTICAL, 0)
        sizer_1.Add((10, 20), 0, 0, 0)
        sizer_1.Add(self.color_button, 0, 0, 0)
        grid_sizer_3.Add(sizer_1, 1, wx.EXPAND, 0)
        grid_sizer_3.Add((5, 5), 0, 0, 0)
        grid_sizer_3.Add((5, 5), 0, 0, 0)
        grid_sizer_3.Add(self.position_radio, 0, wx.EXPAND, 0)
        grid_sizer_3.Add((5, 5), 0, 0, 0)
        grid_sizer_3.Add((5, 5), 0, 0, 0)
        btnsizer.AddButton(self.ok_button)
        btnsizer.AddButton(self.cancel_button)
        btnsizer.Realize()
        grid_sizer_3.Add(btnsizer, 1, wx.EXPAND, 0)
        grid_sizer_3.Add((5, 5), 0, 0, 0)
        grid_sizer_3.Add((5, 5), 0, 0, 0)
        grid_sizer_3.Add((5, 5), 0, 0, 0)
        grid_sizer_3.Add((5, 5), 0, 0, 0)
        self.SetSizer(grid_sizer_3)
        grid_sizer_3.Fit(self)
        self.Layout()
        # end wxGlade
        
    @property
    def canvas_view(self):
        class CanvasAdapter(object):
            def __init__(self, panel):
                self.panel = panel
            
            @property
            def width(self):
                return self.panel.GetSize()[0]
            
            @property
            def height(self):
                return self.panel.GetSize()[1]

        return CanvasAdapter(self.preview_panel)
    
    def on_mouse_wheel(self, event):
        lines = event.GetWheelRotation() / event.GetWheelDelta()
        lines *= event.GetLinesPerAction()
        Publisher.sendMessage('wpcanvas.scrolled', lines=lines)
        
    def on_mouse_left_down(self, event):
        Publisher.sendMessage('wpcanvas.mouse.event', button=0, event=0)
        event.Skip()
        
    def on_mouse_left_up(self, event):
        Publisher.sendMessage('wpcanvas.mouse.event', button=0, event=1)
        event.Skip()
        
    def on_mouse_motion(self, event):
        Publisher.sendMessage('wpcanvas.mouse.motion', x=event.GetX(), y=event.GetY())
        event.Skip()
        
    def on_color_select(self, event):
        color = event.GetValue()
        self.preview_panel.SetBackgroundColour(color)
        self.preview_panel.Refresh()
    
    def on_canvas_changed(self):
        self.preview_panel.Refresh(eraseBackground=False)
        
    def on_canvas_cursor_changed(self, *, cursor):
        self.preview_panel.SetCursor(cursor)
        
    def on_selection_changed(self, event):
        position = event.GetInt()
        Publisher.sendMessage('wallpaper.preview_position_changed', pos_idx=position)
        
    def on_zoom_in(self, event):
        Publisher.sendMessage('wallpaper.zoom', zoom_in=True)
        
    def on_zoom_out(self, event):
        Publisher.sendMessage('wallpaper.zoom', zoom_in=False)

    def on_set_wallpaper(self, event): # wxGlade: WallpaperDialog.<event_handler>
        position = self.position_radio.GetSelection()
        color = self.color_button.GetColour()
        color = (color.Red(), color.Green(), color.Blue())
        Publisher.sendMessage('wallpaper.set', pos_idx=position, color=color)
        self.EndModal(1)

    def on_cancel(self, event): # wxGlade: WallpaperDialog.<event_handler>
        self.EndModal(0)
        
    def on_screen_panel_paint(self, event):
        dc = wx.PaintDC(self.preview_panel)
        #This is required on Linux
        dc.SetBackground(wx.Brush(self.preview_panel.GetBackgroundColour()))
        class PaintedRegion(object):
            def __init__(self):
                self.left = self.top = self.width = self.height = -1
        painted_region = PaintedRegion()
        Publisher.sendMessage('wpcanvas.painted', dc=dc, painted_region=painted_region)
        if painted_region.left != -1:
            clip_region = wx.Region(0, 0, self.preview_panel.GetSize()[0],
                                    self.preview_panel.GetSize()[1])
            clip_region.Subtract(painted_region)
            dc.SetClippingRegionAsRegion(clip_region)
            #Fix for bug in Linux (without this it would clear the entire image
            #when the panel is smaller than the image)
            iter = wx.RegionIterator(clip_region)
            if iter:
                dc.SetClippingRegionAsRegion(clip_region)
                dc.Clear()
        
    def on_preview_changed(self, *, bmp, tiled):
        self.bmp = bmp
        self.tiled = tiled
        self.preview_panel.Refresh()
        
    def on_canvas_zoom_changed(self, *, zoom):
        text = util.get_formatted_zoom(zoom * self.adjust_factor)
        self.zoom_label.SetLabel(text)