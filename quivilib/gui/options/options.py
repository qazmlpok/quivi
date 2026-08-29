#TODO: (2,2) Improve: change the command listbox into a listctrl with columns:
#    (Category / Command / Assigned shortcuts)

import wx
from pubsub import pub as Publisher

from quivilib.gui.options.keyboard_options_panel import KeyboardOptionsPanel
from quivilib.gui.options.language_panel import LanguagePanel
from quivilib.gui.options.mouse_options_panel import MouseOptionsPanel
from quivilib.gui.options.viewing_panel import ViewingPanel
from quivilib.i18n import _
from quivilib.model import Settings
from quivilib.model.command import Command
from quivilib.model.commandenum import FitSettings
from quivilib.model.options import Options

WINDOW_SIZE = (500, 780)


class OptionsDialog(wx.Dialog):
    def __init__(self, parent, fit_choices: list[tuple[str, FitSettings.FitType]], settings: Settings, commands: list[Command],
                 available_languages: list[wx.Language], active_language: wx.Language, save_locally: bool):
        self.fit_choices = fit_choices
        self.save_locally = save_locally
        self.settings = settings
        self.commands = commands
        # begin wxGlade: OptionsDialog.__init__
        wx.Dialog.__init__(self, parent=parent, style=wx.DEFAULT_DIALOG_STYLE|wx.RESIZE_BORDER)
        self.main_notebook = wx.Notebook(self, -1, style=wx.NB_TOP)
        self.mouse_pane = MouseOptionsPanel(self.main_notebook, settings, commands)
        self.language_pane = LanguagePanel(self.main_notebook, available_languages, active_language)
        self.keys_pane = KeyboardOptionsPanel(self.main_notebook,  settings, commands)
        self.viewing_pane = ViewingPanel(self.main_notebook, settings, fit_choices, save_locally)

        self.ok_button = wx.Button(self, wx.ID_OK, _("&OK"))
        self.cancel_button = wx.Button(self, wx.ID_CANCEL, _("&Cancel"))

        self.__set_properties()
        self.__do_layout()
        
        #Do this after do_layout for GetBestSize() to work.
        bestsize = self.GetBestSize()
        self.SetSize(max(bestsize[0], WINDOW_SIZE[0]), max(bestsize[1], WINDOW_SIZE[1]))
        self.Centre()

        self.Bind(wx.EVT_BUTTON, self.on_ok, self.ok_button)
        self.Bind(wx.EVT_BUTTON, self.on_cancel, self.cancel_button)
        # end wxGlade

    def __set_properties(self):
        # begin wxGlade: OptionsDialog.__set_properties
        self.SetTitle(_("Options"))
        self.ok_button.SetDefault()
        # end wxGlade

    def __do_layout(self):
        # begin wxGlade: OptionsDialog.__do_layout
        main_sizer = wx.BoxSizer(wx.VERTICAL)
        btn_sizer = wx.StdDialogButtonSizer()

        self.main_notebook.AddPage(self.viewing_pane, _("&Viewing"))
        self.main_notebook.AddPage(self.keys_pane, _("&Keys"))
        self.main_notebook.AddPage(self.mouse_pane, _("&Mouse"))
        self.main_notebook.AddPage(self.language_pane, _("&Language"))
        main_sizer.Add(self.main_notebook, 1, wx.ALL|wx.EXPAND, 5)
        btn_sizer.AddButton(self.ok_button)
        btn_sizer.AddButton(self.cancel_button)
        btn_sizer.Realize()
        main_sizer.Add(btn_sizer, 0, wx.ALL|wx.EXPAND, 5)
        self.SetSizer(main_sizer)
        self.Layout()
        # end wxGlade

    def on_ok(self, event: wx.CommandEvent): # wxGlade: OptionsDialog.<event_handler>
        opt = Options()
        self.mouse_pane.on_ok(opt)
        self.language_pane.on_ok(opt)
        self.keys_pane.on_ok(opt)
        self.viewing_pane.on_ok(opt)
        
        #TODO: (2,2) Improve: handle errors here
        Publisher.sendMessage('options.update', opt=opt)
        event.Skip()

    def on_cancel(self, event: wx.CommandEvent): # wxGlade: OptionsDialog.<event_handler>
        event.Skip()

# end of class OptionsDialog


if __name__ == '__main__':
    app = wx.App(False)
    class FakeSettings:
        def getint(self, sect, key):
            return 0
        def get(self, sect, key):
            return "0"

    lang = wx.LANGUAGE_ENGLISH_US
    fit = [("Fake", FitSettings.FitType.HEIGHT)]
    dlg = OptionsDialog(None, fit, FakeSettings(), [], [], lang, True)
    dlg.ShowModal()
