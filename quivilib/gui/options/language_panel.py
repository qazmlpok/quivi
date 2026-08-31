import wx
from wx.lib import langlistctrl

from quivilib.control.i18n import LanguageList
from quivilib.model.options import Options


class LanguagePanel(wx.Panel):
    def __init__(self, parent, languages: LanguageList):
        super().__init__(parent=parent, id=-1)

        self.lang_lst = langlistctrl.LanguageListCtrl(
            self, -1,
            style=wx.LC_REPORT | wx.LC_NO_HEADER,
            filter=langlistctrl.LC_ONLY,
            only=languages.all_lang,
            select=languages.current
        )
        self.lang_lst.SetColumnWidth(0, self.lang_lst.GetClientSize()[0])

        self.__set_properties()
        self.__do_layout()

    def __set_properties(self):
        """Initialize dialog checkboxes/dropdowns based on current application settings"""
        #(Nothing to do)
        pass

    def __do_layout(self):
        language_sizer = wx.BoxSizer(wx.VERTICAL)
        language_sizer.Add(self.lang_lst, 1, wx.ALL | wx.EXPAND, 5)

        self.SetSizer(language_sizer)
        self.Layout()
        # end wxGlade

    def on_ok(self, opt: Options):
        opt.language = self.lang_lst.GetLanguage()
