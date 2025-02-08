import wx
from pubsub import pub as Publisher
from pathlib import Path

from quivilib.i18n import _
from quivilib import util

#TODO: (1,3) Refactor: the whole preview_panel and the main window's panel can be
#      refactored into a single class

#The height will potentially need to expand to cover more saved items. The dialog is not static.
WINDOW_SIZE = (450, 175)

class MoveFileDialog(wx.Dialog):
    def __init__(self, parent, settings):
        # begin wxGlade: MoveFileDialog.__init__
        wx.Dialog.__init__(self, parent=parent)
        
        
        self.CurrentPathTxt = wx.TextCtrl(self, wx.ID_ANY, "")
        self.BrowseBtn = wx.Button(self, wx.ID_ANY, _("Browse"))
        self.SavePathBtn = wx.Button(self, wx.ID_ANY, _("+"))   #This would look better with an icon
        self.RightSideSizer = wx.BoxSizer(wx.VERTICAL)
        self.ok_button = wx.Button(self, wx.ID_OK, "")
        self.cancel_button = wx.Button(self, wx.ID_CANCEL, "")

        self.__set_properties()
        self.__do_layout()
        
        #Clear validation messages (item doesn't exist)
        
        #Dynamically populate the right side to include items from the settings.
        
        #Do this after do_layout for GetBestSize() to work.
        bestsize = self.GetBestSize()
        self.SetSize(max(bestsize[0], WINDOW_SIZE[0]), max(bestsize[1], WINDOW_SIZE[1]))
        self.Centre()

        self.Bind(wx.EVT_BUTTON, self.on_open_browse_folder, self.BrowseBtn)
        self.Bind(wx.EVT_BUTTON, self.on_save_path, self.SavePathBtn)
        self.Bind(wx.EVT_BUTTON, self.on_ok, self.ok_button)
        self.Bind(wx.EVT_BUTTON, self.on_cancel, self.cancel_button)
        #Publisher.subscribe(self.on_canvas_zoom_changed, 'wpcanvas.zoom.changed')
        
        #Probably not needed.
        Publisher.sendMessage('move_file.dialog_opened', dialog=self)
        # end wxGlade

    def __set_properties(self):
        # begin wxGlade: MoveFileDialog.__set_properties
        self.SetTitle("Move zip file to another folder")
        self.ok_button.SetDefault()
        self.SetAffirmativeId(self.ok_button.GetId())
        self.SetEscapeId(self.cancel_button.GetId())
        self.CurrentPathTxt.SetValue('')
        # end wxGlade

    def __do_layout(self):
        # begin wxGlade: MoveFileDialog.__do_layout
        MainSizer = wx.BoxSizer(wx.VERTICAL)

        SplitSizer = wx.BoxSizer(wx.HORIZONTAL)
        MainSizer.Add(SplitSizer, 1, wx.EXPAND, 0)

        LeftSideSizer = wx.BoxSizer(wx.VERTICAL)
        SplitSizer.Add(LeftSideSizer, 1, wx.EXPAND, 0)

        label_1 = wx.StaticText(self, wx.ID_ANY, _("Select folder"))
        LeftSideSizer.Add(label_1, 0, wx.LEFT | wx.TOP, 5)

        sizer_3 = wx.BoxSizer(wx.HORIZONTAL)
        LeftSideSizer.Add(sizer_3, 0, wx.ALL, 5)

        self.CurrentPathTxt.SetMinSize((200, 23))
        sizer_3.Add(self.CurrentPathTxt, 0, wx.ALL, 2)

        sizer_3.Add(self.BrowseBtn, 0, wx.ALL, 2)

        self.SavePathBtn.SetMinSize((32, 32))
        self.SavePathBtn.SetToolTip(_("Save"))
        LeftSideSizer.Add(self.SavePathBtn, 0, wx.ALIGN_RIGHT | wx.RIGHT, 7)

        SplitSizer.Add(self.RightSideSizer, 1, wx.EXPAND, 0)

        label_2 = wx.StaticText(self, wx.ID_ANY, _("One"))
        self.RightSideSizer.Add(label_2, 0, wx.ALL, 2)

        label_3 = wx.StaticText(self, wx.ID_ANY, _("Two"))
        self.RightSideSizer.Add(label_3, 0, wx.ALL, 2)

        label_4 = wx.StaticText(self, wx.ID_ANY, _("Three"))
        self.RightSideSizer.Add(label_4, 0, wx.ALL, 2)

        btnsizer = wx.StdDialogButtonSizer()
        MainSizer.Add(btnsizer, 0, wx.ALIGN_RIGHT | wx.ALL, 4)

        btnsizer.AddButton(self.ok_button)

        btnsizer.AddButton(self.cancel_button)

        btnsizer.Realize()

        self.SetSizer(MainSizer)
        self.Layout()
        self.Centre()
        
    def on_open_browse_folder(self, event):  # wxGlade: MoveFileDialog.<event_handler>
        print("Event handler 'on_open_browse_folder' not implemented!")
        event.Skip()

    def on_save_path(self, event):  # wxGlade: MoveFileDialog.<event_handler>
        """ Save (the currently entered?) path to the settings.
        This will be a combination of the path and a "friendly name", so it likely needs another dialog.
        Or, at minimum, another text field.
        Alternatively, this shouldn't be "add", but "Manage saved paths".
        """
        print("Event handler 'on_save_path' not implemented!")
        event.Skip()

    def on_ok(self, event):  # wxGlade: MoveFileDialog.<event_handler>
        print("Event handler 'on_ok' not implemented!")
        #This should handle validation of the path (ensure it's a real folder, etc)
        #and show an error if it's invalid. Returning false will prevent the dialog from closing.
        #return False
        event.Skip()

    def on_cancel(self, event):  # wxGlade: MoveFileDialog.<event_handler>
        event.Skip()
        # end wxGlade


    
    def GetPath(self):
        """ To be called by whatever opened the dialog.
        Retrieves the user selected path.
        """
        return Path(self.CurrentPathTxt.GetValue())

if __name__ == '__main__':
    app = wx.App(False)
    #Need something that can work as fake settings.
    #Or maybe it should be the saved paths extracted from the settings.
    dlg = MoveFileDialog(None, [])
    if dialog.ShowModal() == wx.ID_OK:
        path = Path(dialog.GetPath())
        print(f"Selected: {path}")
    else:
        print("Cancel clicked.")
    dialog.Destroy()


