#TODO: (2,2) Improve: change the command listbox into a listctrl with columns:
#    (Category / Command / Assigned shortcuts)

import wx
from pubsub import pub as Publisher

WINDOW_SIZE = (400, 480)

class DebugDialog(wx.Dialog):
    def __init__(self, parent):
        # begin wxGlade: OptionsDialog.__init__
        wx.Dialog.__init__(self, parent=parent, style=wx.DEFAULT_DIALOG_STYLE|wx.RESIZE_BORDER)
        
        self.ok_button = wx.Button(self, wx.ID_OK, "&OK")

        self.__set_properties()
        self.__do_layout()
        
        #Do this after do_layout for GetBestSize() to work.
        bestsize = self.GetBestSize()
        self.SetSize(max(bestsize[0], WINDOW_SIZE[0]), max(bestsize[1], WINDOW_SIZE[1]))
        self.Centre()

    def __set_properties(self):
        # begin wxGlade: OptionsDialog.__set_properties
        self.SetTitle("Debug information")
        # end wxGlade
        
        self.ok_button.SetDefault()

    def __do_layout(self):
        # begin wxGlade: OptionsDialog.__do_layout
        main_sizer = wx.BoxSizer(wx.VERTICAL)
        
        self.Layout()
        # end wxGlade


    def on_ok(self, event): # wxGlade: OptionsDialog.<event_handler>
        event.Skip()

    def on_cancel(self, event): # wxGlade: OptionsDialog.<event_handler>
        event.Skip()
        
# end of class OptionsDialog


if __name__ == '__main__':
    app = wx.App(False)
    dlg = DebugDialog(None)
    dlg.ShowModal()
