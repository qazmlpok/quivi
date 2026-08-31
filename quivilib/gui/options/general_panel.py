import sys

import wx

from quivilib.i18n import _
from quivilib.model import Settings
from quivilib.model.options import GeneralOptions


class GeneralPanel(wx.Panel):
    def __init__(self, parent: wx.Window, settings: Settings, save_locally: bool):
        super().__init__(parent=parent, id=-1)
        self.save_locally = save_locally
        self.settings = settings

        self._init_general()

        self.__set_properties()
        self.__do_layout()

    def _init_general(self):
        self.bg_color_sizer_staticbox = wx.StaticBox(self, -1, _("Background color"))
        self.bg_color_default_rdo = wx.RadioButton(self.bg_color_sizer_staticbox, -1, _("Default system color"), style=wx.RB_GROUP)
        self.bg_color_custom_rdo = wx.RadioButton(self.bg_color_sizer_staticbox, -1, _("Custom color:"))
        self.bg_color_picker = wx.ColourPickerCtrl(self.bg_color_sizer_staticbox, -1)
        self.dark_mode_system_rdo = DarkModeRadioBox(self)

        self.real_fullscreen_chk = wx.CheckBox(self, -1, _("Hide menu and status on full screen"))
        self.open_first_chk = wx.CheckBox(self, -1, _("Open first image of the folder automatically"))
        self.settings_local_chk = wx.CheckBox(self, -1, _("Portable mode (save settings inside the program folder)"))
        self.auto_fullscreen_chk = wx.CheckBox(self, -1, _("Remember full screen on close"))

    def __set_properties(self):
        """Initialize dialog checkboxes/dropdowns based on current application settings"""
        if self.settings.get('Options', 'CustomBackground') == '1':
            self.bg_color_custom_rdo.SetValue(True)
        else:
            self.bg_color_default_rdo.SetValue(True)
        darkmode = self.settings.getint('Options', 'DarkMode')
        self.dark_mode_system_rdo.SetSelection(darkmode)

        color = self.settings.get('Options', 'CustomBackgroundColor').split(',')
        color = wx.Colour(*[int(c) for c in color])
        self.bg_color_picker.SetColour(color)

        real_fullscreen = (self.settings.get('Options', 'RealFullscreen') == '1')
        self.real_fullscreen_chk.SetValue(real_fullscreen)
        open_first = (self.settings.get('Options', 'OpenFirst') == '1')
        self.open_first_chk.SetValue(open_first)
        auto_fullscreen = (self.settings.get('Options', 'AutoFullscreen') == '1')
        self.auto_fullscreen_chk.SetValue(auto_fullscreen)

        self.settings_local_chk.SetValue(self.save_locally)

    def __do_layout(self):
        viewing_sizer = wx.BoxSizer(wx.VERTICAL)

        fit_outer = wx.BoxSizer(wx.HORIZONTAL)
        fit_inner1 = wx.BoxSizer(wx.VERTICAL)
        fit_inner2 = wx.BoxSizer(wx.VERTICAL)
        fit_outer.Add(fit_inner1, 1, wx.RIGHT | wx.EXPAND, 10)
        fit_outer.Add(fit_inner2, 0, wx.RIGHT | wx.EXPAND, 10)
        viewing_sizer.Add(fit_outer, 0, wx.TOP | wx.BOTTOM | wx.EXPAND, 5)

        bg_color_sizer = wx.StaticBoxSizer(self.bg_color_sizer_staticbox, wx.VERTICAL)
        custom_bg_color_sizer = wx.BoxSizer(wx.HORIZONTAL)
        bg_color_sizer.Add(self.bg_color_default_rdo, 0, wx.LEFT | wx.RIGHT | wx.TOP, 5)
        custom_bg_color_sizer.Add(self.bg_color_custom_rdo, 0, wx.ALIGN_CENTER_VERTICAL, 0)
        custom_bg_color_sizer.Add(self.bg_color_picker, 0, wx.LEFT | wx.RIGHT | wx.EXPAND, 5)
        bg_color_sizer.Add(custom_bg_color_sizer, 1, wx.ALL | wx.EXPAND, 5)
        viewing_sizer.Add(bg_color_sizer, 0, wx.LEFT | wx.RIGHT | wx.TOP | wx.EXPAND, 5)

        self.dark_mode_system_rdo.do_layout(viewing_sizer)

        viewing_sizer.Add(self.real_fullscreen_chk, 0, wx.LEFT | wx.RIGHT | wx.TOP, 5)
        viewing_sizer.Add(self.open_first_chk, 0, wx.LEFT | wx.RIGHT | wx.TOP, 5)
        viewing_sizer.Add(self.settings_local_chk, 0, wx.LEFT | wx.RIGHT | wx.TOP, 5)
        viewing_sizer.Add(self.auto_fullscreen_chk, 0, wx.LEFT | wx.RIGHT | wx.TOP, 5)

        self.SetSizer(viewing_sizer)

    def on_ok(self):
        opt = GeneralOptions()
        opt.custom_bg = self.bg_color_custom_rdo.GetValue()
        opt.custom_bg_color = self.bg_color_picker.GetColour()

        opt.save_locally = self.settings_local_chk.GetValue()
        opt.real_fullscreen = self.real_fullscreen_chk.GetValue()
        opt.open_first = self.open_first_chk.GetValue()
        opt.auto_fullscreen = self.auto_fullscreen_chk.GetValue()
        opt.darkmode = self.dark_mode_system_rdo.GetSelection()
        return opt

# end of class OptionsDialog

class DarkModeRadioBox():
    """Encapsulation for the dark mode control, sizer, and radio buttons. The standard RadioBox does not give enough flexibility for what I want.
    This isn't intended to be reusable at all."""

    def __init__(self, parent: wx.Window):
        self.show_warning_label = sys.platform == 'win32'

        self.static_box = wx.StaticBox(parent, -1, _("Dark Mode"))
        self.static_box_sizer = wx.StaticBoxSizer(self.static_box, wx.VERTICAL)

        self.radio_default = wx.RadioButton(self.static_box, -1, _("System Default"), style=wx.RB_GROUP)
        self.radio_light = wx.RadioButton(self.static_box, -1, _("Light"))
        self.radio_dark = wx.RadioButton(self.static_box, -1, _("Dark"))

        self.dark_mode_warning_lbl = None
        if self.show_warning_label:
            self.dark_mode_warning_lbl = wx.StaticText(self.static_box, -1, _("Requires restart to take effect"))
            self.dark_mode_warning_lbl.SetForegroundColour(wx.Colour(0xc4, 0x32, 0x55))
            self.dark_mode_warning_lbl.SetFont(wx.Font(10, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL, False, ""))

    def do_layout(self, sizer: wx.Sizer):
        radio_sizer = wx.BoxSizer(wx.HORIZONTAL)
        radio_sizer.Add(self.radio_default, 0, wx.LEFT | wx.RIGHT | wx.ALIGN_LEFT, 5)
        radio_sizer.Add(self.radio_light, 0, wx.LEFT | wx.RIGHT | wx.ALIGN_LEFT, 5)
        radio_sizer.Add(self.radio_dark, 0, wx.LEFT | wx.RIGHT | wx.ALIGN_LEFT, 5)

        if self.dark_mode_warning_lbl:
            self.static_box_sizer.Add(self.dark_mode_warning_lbl, 0, wx.ALIGN_RIGHT | wx.RIGHT, 10)
        self.static_box_sizer.Add(radio_sizer, 0, wx.ALIGN_LEFT | wx.TOP | wx.BOTTOM, 5)
        sizer.Add(self.static_box_sizer, 0, wx.EXPAND | wx.LEFT | wx.RIGHT | wx.TOP, 5)

    def GetSelection(self):
        if (self.radio_light.GetValue()):
            return 1
        if (self.radio_dark.GetValue()):
            return 2
        return 0

    def SetSelection(self, value: int):
        value = max(0, min(value, 2))
        self.radio_default.SetValue(value == 0)
        self.radio_light.SetValue(value == 1)
        self.radio_dark.SetValue(value == 2)
