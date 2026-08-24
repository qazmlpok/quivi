import wx

from quivilib.i18n import _
from quivilib import meta
from quivilib.resources import images

# begin wxGlade: dependencies
# end wxGlade

# begin wxGlade: extracode
import wx.lib.agw.hyperlink as hl
# end wxGlade

class AboutDialog(wx.Dialog):
    def __init__(self, *args, **kwds):
        # begin wxGlade: AboutDialog.__init__
        kwds["style"] = wx.DEFAULT_DIALOG_STYLE|wx.RESIZE_BORDER
        wx.Dialog.__init__(self, *args, **kwds)
        self.icon_bmp = wx.StaticBitmap(self, -1, images.quivi.Bitmap)
        self.name_lbl = wx.StaticText(self, -1, f'{meta.APPNAME} {meta.VERSION}')
        self.copyright_txt = wx.TextCtrl(self, -1, '', style=wx.TE_MULTILINE|wx.TE_READONLY|wx.TE_NOHIDESEL|wx.NO_BORDER)
        self.project_link = hl.HyperLinkCtrl(self, -1, meta.URL, URL=meta.URL)
        self.set_link_color()

        self.ok_btn = wx.Button(self, wx.ID_OK, _("&OK"))
        self.ok_btn.Bind(wx.EVT_BUTTON, self.on_ok_click)

        self.__set_properties()
        self.__do_layout()
        # end wxGlade

    def __set_properties(self):
        # begin wxGlade: AboutDialog.__set_properties
        self.SetTitle(_("About"))
        self.name_lbl.SetFont(wx.Font(16, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL, False, ""))
        # end wxGlade
        self.copyright_txt.SetMinSize(wx.Size(300, -1))
        color = wx.SystemSettings.GetColour(wx.SYS_COLOUR_BTNFACE)
        self.copyright_txt.SetBackgroundColour(color)
        self.copyright_txt.Refresh()
        
        txt = meta.COPYRIGHT
        txt += '\n'
        if meta.USE_FREEIMAGE:
            from pyfreeimage import library
            lib = library.load()
            txt += '\n'
            txt += lib.GetCopyrightMessage().decode("utf-8")
            txt += '\nFreeImage is used under the FreeImage Public License, version 1.0'
            txt += '\n\nThis program uses source from FreeImagePy (https://freeimagepy.sourceforge.net/) under the FreeImage Public License, version 1.0'
            
        self.copyright_txt.SetValue(txt) 

    def __do_layout(self):
        # begin wxGlade: AboutDialog.__do_layout
        main_sizer = wx.BoxSizer(wx.VERTICAL)
        stddialog_sizer = wx.StdDialogButtonSizer()
        header_sizer = wx.BoxSizer(wx.HORIZONTAL)
        header_v_sizer = wx.BoxSizer(wx.VERTICAL)
        header_sizer.Add(self.icon_bmp, 0, wx.LEFT|wx.RIGHT|wx.TOP, 10)
        header_v_sizer.Add(self.name_lbl, 0, wx.LEFT|wx.RIGHT|wx.TOP|wx.EXPAND, 10)
        header_v_sizer.Add(self.project_link, 1, wx.LEFT|wx.RIGHT, 10)
        header_sizer.Add(header_v_sizer, 1, wx.EXPAND, 0)
        main_sizer.Add(header_sizer, 0, wx.EXPAND, 0)
        main_sizer.Add(self.copyright_txt, 1, wx.LEFT|wx.RIGHT|wx.TOP|wx.EXPAND, 10)
        stddialog_sizer.AddButton(self.ok_btn)
        stddialog_sizer.Realize()
        main_sizer.Add(stddialog_sizer, 0, wx.EXPAND|wx.ALL, 10)
        self.SetSizer(main_sizer)
        self.Layout()
        main_sizer.Fit(self)
        self.Centre()
        # end wxGlade
        
    def on_ok_click(self, event):
        self.EndModal(1)

    def set_link_color(self):
        link = wx.BLUE
        visited = wx.Colour(79, 47, 79)
        if wx.SystemSettings.GetAppearance().IsDark():
            link = wx.Colour(0x87, 0xce, 0xfa)
            visited = wx.Colour(0x6d, 0x4b, 0x8d)

        #This should be set up to change on light/dark switch, but this really isn't worth the effort.
        self.project_link.SetColours(link=link, visited=visited, rollover=link)
        self.project_link.UpdateLink()

# end of class AboutDialog

if __name__ == '__main__':
    app = wx.App(False)
    dlg = AboutDialog(None)
    dlg.ShowModal()
