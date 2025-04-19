import os, sys
import wx
from pubsub import pub as Publisher
from pathlib import Path

from quivilib.i18n import _
from quivilib import util
from quivilib.model.savedpath import SavedPaths

#The height will potentially need to expand to cover more saved items. The dialog is not static.
WINDOW_SIZE = (450, 200)

class MoveFileDialog(wx.Dialog):
    def __init__(self, parent, settings, name='', start_path=''):
        #The path to the currently opened container. This is used as the starting dir when doing browse,
        #but not for anything else
        self.current_path = start_path
        self.container_name = name
        #Need to store this for saving the settings after.
        self.paths_modified = False
        self._settings = settings
        self.saved_folders = SavedPaths(settings)
        # begin wxGlade: MoveFileDialog.__init__
        wx.Dialog.__init__(self, parent=parent)
        
        
        self.MainSizer = wx.BoxSizer(wx.VERTICAL)
        self.CurrentPathTxt = wx.TextCtrl(self, wx.ID_ANY, "")
        self.BrowseBtn = wx.Button(self, wx.ID_ANY, _("Browse"))
        self.SavePathBtn = wx.Button(self, wx.ID_ANY, "+")      #This would look better with an icon
        self.RightSideBox = wx.StaticBox(self, wx.ID_ANY, _("Saved paths"))
        self.RightSideSizer = wx.StaticBoxSizer(self.RightSideBox, wx.VERTICAL)
        self.SavedPathNameTxt = wx.TextCtrl(self, wx.ID_ANY, "")
        self.ValidationMessage = wx.StaticText(self, wx.ID_ANY, "")
        self.ok_button = wx.Button(self, wx.ID_OK, "")
        self.cancel_button = wx.Button(self, wx.ID_CANCEL, "")

        self.__set_properties()
        self.__do_layout()
        self.__layout_saved_folders(self.saved_folders)
        #Need to call Layout here because I split __do_layout()
        self.SetSizer(self.MainSizer)
        self.Layout()
        
        #Do this after do_layout for GetBestSize() to work.
        bestsize = self.GetBestSize()
        self.SetSize(max(bestsize[0], WINDOW_SIZE[0]), max(bestsize[1], WINDOW_SIZE[1]))
        self.Centre()

        self.Bind(wx.EVT_BUTTON, self.on_open_browse_folder, self.BrowseBtn)
        self.Bind(wx.EVT_BUTTON, self.on_save_path, self.SavePathBtn)
        self.Bind(wx.EVT_BUTTON, self.on_ok, self.ok_button)
        self.Bind(wx.EVT_BUTTON, self.on_cancel, self.cancel_button)
        
        #Probably not needed.
        Publisher.sendMessage('move_file.dialog_opened', dialog=self)
        # end wxGlade

    def __set_properties(self):
        # begin wxGlade: MoveFileDialog.__set_properties
        self.SetTitle(_("Move zip file to another folder"))
        self.ok_button.SetDefault()
        self.SetAffirmativeId(self.ok_button.GetId())
        self.SetEscapeId(self.cancel_button.GetId())
        self.CurrentPathTxt.SetValue('')
        self.SavedPathNameTxt.SetValue('')
        self.ValidationMessage.SetLabel('')
        self.ValidationMessage.SetForegroundColour(wx.Colour(255, 0, 0))
        # end wxGlade

    def __do_layout(self):
        # begin wxGlade: MoveFileDialog.__do_layout
        if (self.container_name):
            name_lbl = wx.StaticText(self, wx.ID_ANY, self.container_name, style=wx.ST_ELLIPSIZE_END)
            name_lbl.SetMaxSize((360, -1))
            self.MainSizer.Add(name_lbl, 0, wx.EXPAND | wx.ALL, 4)
        
        split_sizer = wx.BoxSizer(wx.HORIZONTAL)
        self.MainSizer.Add(split_sizer, 1, wx.EXPAND, 0)

        left_side_sizer = wx.BoxSizer(wx.VERTICAL)
        split_sizer.Add(left_side_sizer, 2, wx.EXPAND | wx.RIGHT, 8)

        select_folder_lbl = wx.StaticText(self, wx.ID_ANY, _("Select folder"))
        left_side_sizer.Add(select_folder_lbl, 0, wx.LEFT | wx.TOP, 5)

        select_dir_sizer = wx.BoxSizer(wx.HORIZONTAL)
        left_side_sizer.Add(select_dir_sizer, 0, wx.ALL, 5)

        self.CurrentPathTxt.SetMinSize((200, 23))
        select_dir_sizer.Add(self.CurrentPathTxt, 0, wx.ALL | wx.ALIGN_CENTER_VERTICAL, 2)

        select_dir_sizer.Add(self.BrowseBtn, 0, wx.ALL | wx.ALIGN_CENTER_VERTICAL, 2)
        
        save_path_sizer = wx.StaticBoxSizer(wx.StaticBox(self, wx.ID_ANY, _("Save path")), wx.HORIZONTAL)
        left_side_sizer.Add(save_path_sizer, 1, wx.EXPAND | wx.LEFT | wx.RIGHT, 16)
        
        name_lbl = wx.StaticText(self, wx.ID_ANY, _("Name:"))
        save_path_sizer.Add(name_lbl, 0, wx.ALIGN_CENTER_VERTICAL | wx.RIGHT, 5)

        save_path_sizer.Add(self.SavedPathNameTxt, 1, wx.ALIGN_CENTER_VERTICAL, 0)
        if sys.platform == 'win32':
            #This works in Win fine but breaks GTK.
            self.SavePathBtn.SetMinSize((24, 24))
        self.SavePathBtn.SetToolTip(_("Save"))
        save_path_sizer.Add(self.SavePathBtn, 0, wx.ALIGN_CENTER_VERTICAL | wx.LEFT, 4)

        split_sizer.Add(self.RightSideSizer, 1, wx.EXPAND | wx.RIGHT, 8)
        #Contents of RightSideSizer added dynamically later.
        
        padding_sizer = wx.BoxSizer(wx.HORIZONTAL)
        self.MainSizer.Add(padding_sizer, 0, wx.ALL | wx.EXPAND, 4)
        padding_sizer.Add(self.ValidationMessage, 0, wx.EXPAND | wx.LEFT, 10)

        btnsizer = wx.StdDialogButtonSizer()
        self.MainSizer.Add(btnsizer, 0, wx.ALIGN_RIGHT | wx.ALL, 4)

        btnsizer.AddButton(self.ok_button)
        btnsizer.AddButton(self.cancel_button)
        btnsizer.Realize()
    def __layout_saved_folders(self, saved_folders):
        """ Uses a loop to add the saved folders to the right side sizer.
        There is no limit to the number of folders that could be saved; some kind of special handling
        is probably needed for large lists. Nothing is implemented until needed.
        """
        self.RightSideSizer.Clear()
        
        if (saved_folders.count() == 0):
            #Add text saying "No saved folders"?
            return
        
        for (name, path) in saved_folders:
            def _event_handler(event, _path=path):
                self.CurrentPathTxt.SetValue(str(_path))
                event.Skip()
            #These are buttons for easy use of events; I think statictext can't have events
            #Might be able to use a listctrl, maybe?
            btn = wx.Button(self.RightSideBox, wx.ID_ANY, name)
            self.RightSideSizer.Add(btn, 0, 0)
            self.Bind(wx.EVT_BUTTON, _event_handler, btn)
    
    def on_open_browse_folder(self, event):  # wxGlade: MoveFileDialog.<event_handler>
        """ Open a standard directory browse dialog. This will be the location the file is moved to
        (this control only sets the text field; the actual move occurs later)
        If a path is currently filled in, the dialog will open there; otherwise it's the current location
        """
        dialog = wx.DirDialog(self, _('Choose a directory:'),
                              style=wx.DD_DEFAULT_STYLE|wx.DD_DIR_MUST_EXIST)
        #Reminder; CurrentPathTxt is freely editable. SetPath appears to do nothing if it doesn't exist.
        val = self.CurrentPathTxt.GetValue()
        if val is not None and val.strip() != '':
            dialog.SetPath(val)
        elif self.current_path != '':
            dialog.SetPath(self.current_path)
        if dialog.ShowModal() == wx.ID_OK:
            self.CurrentPathTxt.SetValue(dialog.GetPath())
    #
    def on_save_path(self, event):  # wxGlade: MoveFileDialog.<event_handler>
        """ Save the currently entered path to the settings.
        This will be a combination of the path and a "friendly name", so it likely needs another dialog.
        Or, at minimum, another text field.
        Alternatively, this shouldn't be "add", but "Manage saved paths".
        """
        newpath = self.CurrentPathTxt.GetValue()
        newname = self.SavedPathNameTxt.GetValue()
        
        if not newpath:
            self.ValidationMessage.SetLabel(_("A path must be entered to save"))
            return
        if not newname:
            self.ValidationMessage.SetLabel(_("A name is required for the path to save"))
            return
        if len(newname) > 25:
            #Even this is a lot; the display gets wonky with long names.
            self.ValidationMessage.SetLabel(_("Maximum length for a name is 25 characters"))
            return
        if not self.saved_folders.path_is_valid(newname, newpath):
            #The error message is an implementation detail but I don't want to put the message in savedpath.
            self.ValidationMessage.SetLabel(_("The '|' character cannot appear in the name or path"))
            return
        if self.saved_folders.path_already_exists(newpath):
            self.ValidationMessage.SetLabel(_("The entered path is already saved"))
            return
        
        #Save to settings; this will be saved to disk when the modal is closed.
        self.saved_folders.add_new(newname, newpath)
        self.paths_modified = True
        #Need to re-apply layout. Fit is also necessary; not sure why.
        self.__layout_saved_folders(self.saved_folders)
        self.RightSideSizer.Layout()
        self.Fit()
        
        #Clear name, but not path
        self.SavedPathNameTxt.SetValue('')
        self.ValidationMessage.SetLabel('')

    def on_ok(self, event):  # wxGlade: MoveFileDialog.<event_handler>
        newpath = self.CurrentPathTxt.GetValue()
        if not newpath or not os.path.isdir(newpath):
            self.ValidationMessage.SetLabel(_("The path must be a valid directory"))
            #It also needs to be writable, but I'd rather just let the move throw.
            return False
        if self.current_path and self.current_path == newpath:
            self.ValidationMessage.SetLabel(_("The target path is the same as the file's current location"))
            return False
        #Anything else to check here?

        self._save_settings()
        event.Skip()

    def on_cancel(self, event):  # wxGlade: MoveFileDialog.<event_handler>
        self._save_settings()
        event.Skip()
        # end wxGlade

    def _save_settings(self):
        if not self.paths_modified:
            return
        try:
            self.saved_folders.save(self._settings)
        except:
            log.error("Failed to save paths")

    
    def GetPath(self):
        """ To be called by whatever opened the dialog.
        Retrieves the user selected path.
        """
        return Path(self.CurrentPathTxt.GetValue())

if __name__ == '__main__':
    app = wx.App(False)
    #Need something that can work as fake saved_folders.
    #Or maybe it should be the saved paths extracted from the settings.
    #-This is no longer just a list of tuples.
    saved_folders = [('One', 'E:/temp'),('Two', 'E:/temp/temp'),('Three', 'E:/temp/temp/temp'),('Four_but also this is much longer', 'E:/temp/temp/temp/temp'),]
    dlg = MoveFileDialog(None, saved_folders)
    if dialog.ShowModal() == wx.ID_OK:
        path = Path(dialog.GetPath())
        print(f"Selected: {path}")
    else:
        print("Cancel clicked.")
    dialog.Destroy()


