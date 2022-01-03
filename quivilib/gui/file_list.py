from __future__ import absolute_import
from quivilib.gui.file_list_view.list_ctrl import FileList
from quivilib.gui.file_list_view import thumb as tc
from quivilib.gui import art

import wx
import wx.lib.buttonpanel as bp
from wx.lib.pubsub import pub as Publisher


def _handle_error(exception, args, kwargs):
    self = args[0]
    self.handle_error(exception)


class FileListPanel(wx.Panel):
    def __init__(self, parent):
        wx.Panel.__init__(self, parent)
        
        self.buttons = []
        self.update_fns = []
        
        sizer = wx.BoxSizer(wx.VERTICAL)
        
        self.tool_bar = bp.ButtonPanel(self)
        
        self.file_list = FileList(self)
        self.thumb_list = tc.ThumbnailCtrl(self, thumboutline=tc.THUMB_OUTLINE_RECT)
        
        sizer.Add(self.tool_bar, 0, wx.EXPAND)
        sizer.Add(self.file_list, 1, wx.EXPAND, 0)
        sizer.Add(self.thumb_list, 1, wx.EXPAND, 0)
        sizer.Hide(self.thumb_list, recursive=True)
        self.tool_bar.GetBPArt().SetColor(bp.BP_SELECTION_BRUSH_COLOUR, wx.Colour(242, 242, 235))
        self.tool_bar.GetBPArt().SetColor(bp.BP_SELECTION_PEN_COLOUR, wx.Colour(206, 206, 195))
        self.tool_bar.SetStyle(bp.BP_DEFAULT_STYLE)
        self.tool_bar.GetBPArt().SetMetric(bp.BP_BORDER_SIZE, 0)
        self.tool_bar.DoLayout()
        self.SetSizer(sizer)
        self.Fit()
        
        self.thumb_list.SetCaptionFont(wx.NORMAL_FONT)
        self.thumb_list.SetSelectionColour()
        
        self.Bind(wx.EVT_ENTER_WINDOW, self.on_mouse_enter)
        self.file_list.Bind(wx.EVT_ENTER_WINDOW, self.on_mouse_enter)
        self.thumb_list._scrolled.Bind(wx.EVT_ENTER_WINDOW, self.on_mouse_enter)
        self.Bind(wx.EVT_IDLE, self.on_idle)
        
        Publisher.subscribe(self.on_toolbar_built, 'toolbar.built')
        Publisher.subscribe(self.on_toolbar_labels_changed, 'toolbar.labels.changed')
        Publisher.subscribe(self.on_favorite_opened, 'favorite.opened')
        
        self._delay_favorite = None
        self._show_thumbnails = False
        
    @property
    def current_view(self):
        return self.thumb_list if self._show_thumbnails else self.file_list
        
    def toggle_thumbnails(self):
        self._show_thumbnails = not self._show_thumbnails
        self.GetSizer().Show(self.thumb_list, show=self._show_thumbnails, recursive=True)
        self.GetSizer().Show(self.file_list, show=not self._show_thumbnails, recursive=True)
        self.current_view.show()
        self.Layout()
        
    def is_thumbnails(self):
        return self._show_thumbnails
        
    def on_mouse_enter(self, event):
        self.current_view.SetFocus()
    
    def on_toolbar_built(self, message):
        commands = message.data
        
        #TODO: (2,2) Refactor: This shouldn't be hard coded
        #This must reflect the commands tuple from the message
        bmp_ids = (wx.ART_FOLDER_OPEN, wx.ART_ADD_BOOKMARK, wx.ART_DEL_BOOKMARK,
                   wx.ART_GO_DIR_UP, art.ART_THUMBNAIL_VIEW)
        
        #TODO: (3,3) Refactor: change add/del bookmark to a single button
        
        for cmd, bmp_id in zip(commands, bmp_ids):
            bmp = wx.ArtProvider.GetBitmap(bmp_id, wx.ART_TOOLBAR, (16, 16))
            kind = wx.ITEM_CHECK if cmd.checkable else wx.ITEM_NORMAL
            button = bp.ButtonInfo(self.tool_bar, -1, bmp, kind=kind,
                                   shortHelp=cmd.clean_name, longHelp=cmd.description)
            self.tool_bar.AddButton(button)
            self.buttons.append(button)
            self.update_fns.append(cmd.update_function)
            def event_fn(event, cmd=cmd):
                try:
                    cmd()
                except Exception, e:
                    self.handle_error(e)
            self.Bind(wx.EVT_BUTTON, event_fn, id=button.GetId())
        
        self.tool_bar.DoLayout()
        self.Fit()
        
        if self._delay_favorite is not None:
            class Dummy(): pass
            message = Dummy()
            message.data = self._delay_favorite
            self.on_favorite_opened(message)
        
    def on_toolbar_labels_changed(self, message):
        commands = message.data
        for cmd, button in zip(commands, self.buttons):
            button.SetShortHelp(cmd.clean_name)
            button.SetLongHelp(cmd.description)
            
    def on_favorite_opened(self, message):
        favorite = message.data
        if not self.buttons:
            #Buttons not created yet, delay notification
            self._delay_favorite = favorite
            return 
        if favorite:
            self.buttons[1].Status = 'Disabled'
            self.buttons[2].Status = 'Normal'
        else:
            self.buttons[1].Status = 'Normal'
            self.buttons[2].Status = 'Disabled'
            
    def on_idle(self, event):
        class FakeUpdateUIEvent(object):
            checked = None
            def Check(self, check):
                self.checked = check
        for button, fn in zip(self.buttons, self.update_fns):
            if not fn:
                continue
            e = FakeUpdateUIEvent()
            fn(e)
            if e.checked is not None:
                if button.Status not in ('Hover', 'Pressed'):
                    button.SetToggled(e.checked)
                    button.Status = 'Toggled' if e.checked else 'Normal'
            
    def save(self, settings_lst):
        self.file_list.save(settings_lst)
    
    def load(self, settings):
        self.file_list.load(settings)
        
    def handle_error(self, exception):
        self.Parent.handle_error(exception)
