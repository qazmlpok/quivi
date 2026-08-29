import sys

import wx

from quivilib.i18n import _
from quivilib.model import Settings
from quivilib.model.commandenum import FitSettings
from quivilib.model.options import Options


class ViewingPanel(wx.Panel):
    def __init__(self, parent: wx.Window, settings: Settings, fit_choices: list[tuple[str, FitSettings.FitType]], save_locally: bool):
        super().__init__(parent=parent, id=-1)
        self.fit_choices = fit_choices
        self.save_locally = save_locally
        self.settings = settings

        self._init_viewing()

        self.__set_properties()
        self.__do_layout()

        self.Bind(wx.EVT_COMBOBOX, self.on_fit_select, self.fit_cbo)

    def _init_viewing(self):
        self.bg_color_sizer_staticbox = wx.StaticBox(self, -1, _("Background color"))
        self.fit_label = wx.StaticText(self, -1, _("Fit"))
        self.fit_cbo = wx.ComboBox(self, -1, choices=[], style=wx.CB_DROPDOWN | wx.CB_READONLY)
        self.width_label = wx.StaticText(self, -1, _("Width"))
        self.width_txt = wx.TextCtrl(self, -1, "800")
        self.start_dir_lbl = wx.StaticText(self, -1, _("Start directory"))
        self.start_dir_picker = wx.DirPickerCtrl(self, -1)
        self.bg_color_default_rdo = wx.RadioButton(self.bg_color_sizer_staticbox, -1, _("Default system color"), style=wx.RB_GROUP)
        self.bg_color_custom_rdo = wx.RadioButton(self.bg_color_sizer_staticbox, -1, _("Custom color:"))
        self.bg_color_picker = wx.ColourPickerCtrl(self.bg_color_sizer_staticbox, -1)
        self.dark_mode_system_rdo = DarkModeRadioBox(self)

        self.real_fullscreen_chk = wx.CheckBox(self, -1, _("Hide menu and status on full screen"))
        self.open_first_chk = wx.CheckBox(self, -1, _("Open first image of the folder automatically"))
        self.settings_local_chk = wx.CheckBox(self, -1, _("Portable mode (save settings inside the program folder)"))
        self.auto_fullscreen_chk = wx.CheckBox(self, -1, _("Remember full screen on close"))
        self.right_to_left_chk = wx.CheckBox(self, -1, _("View images right-to-left"))
        self.scroll_at_bottom_chk = wx.CheckBox(self, -1, _("Scroll horizontally when scrolling past end of image"))
        self.placeholder_autodelete_chk = wx.CheckBox(self, -1, _("Delete placeholders when opening"))
        self.placeholder_single_chk = wx.CheckBox(self, -1, _("Only allow a single placeholder"))
        self.placeholder_autoopen_chk = wx.CheckBox(self, -1, _("Automatically jump to placeholder page on open"))
        self.placeholder_separate_chk = wx.CheckBox(self, -1, _("Use separate menus for favorites and placeholders"))

    def __set_properties(self):
        setting_fit_type = FitSettings.get_fittype(self.settings.get('Options', 'FitType'))
        for name, fit_type in self.fit_choices:
            idx = self.fit_cbo.Append(name, fit_type)
            if fit_type == setting_fit_type:
                self.fit_cbo.SetSelection(idx)
                self._update_custom_fit_display(fit_type)

        self.width_txt.SetValue(self.settings.get('Options', 'FitWidthCustomSize'))

        self.start_dir_picker.SetPath(self.settings.get('Options', 'StartDir'))

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
        use_right_to_left = (self.settings.get('Options', 'UseRightToLeft') == '1')
        self.right_to_left_chk.SetValue(use_right_to_left)
        scroll_at_bottom = (self.settings.get('Options', 'HorizontalScrollAtBottom') == '1')
        self.scroll_at_bottom_chk.SetValue(scroll_at_bottom)
        placeholder_delete = (self.settings.get('Options', 'PlaceholderDelete') == '1')
        self.placeholder_autodelete_chk.SetValue(placeholder_delete)
        placeholder_single = (self.settings.get('Options', 'PlaceholderSingle') == '1')
        self.placeholder_single_chk.SetValue(placeholder_single)
        placeholder_autoopen = (self.settings.get('Options', 'PlaceholderAutoOpen') == '1')
        self.placeholder_autoopen_chk.SetValue(placeholder_autoopen)
        placeholder_separate = (self.settings.get('Options', 'PlaceholderSeparateMenu') == '1')
        self.placeholder_separate_chk.SetValue(placeholder_separate)

        self.settings_local_chk.SetValue(self.save_locally)

    def __do_layout(self):
        viewing_sizer = wx.BoxSizer(wx.VERTICAL)

        fit_outer = wx.BoxSizer(wx.HORIZONTAL)
        fit_inner1 = wx.BoxSizer(wx.VERTICAL)
        fit_inner2 = wx.BoxSizer(wx.VERTICAL)
        fit_outer.Add(fit_inner1, 1, wx.RIGHT | wx.EXPAND, 10)
        fit_outer.Add(fit_inner2, 0, wx.RIGHT | wx.EXPAND, 10)
        viewing_sizer.Add(fit_outer, 0, wx.TOP | wx.BOTTOM | wx.EXPAND, 5)

        fit_inner1.Add(self.fit_label, 0, wx.LEFT | wx.RIGHT | wx.TOP, 5)
        fit_inner1.Add(self.fit_cbo, 0, wx.LEFT | wx.RIGHT | wx.TOP, 5)
        fit_inner2.Add(self.width_label, 0, wx.LEFT | wx.RIGHT | wx.TOP | wx.EXPAND, 5)
        fit_inner2.Add(self.width_txt, 0, wx.LEFT | wx.RIGHT | wx.TOP | wx.EXPAND, 5)

        viewing_sizer.Add(self.start_dir_lbl, 0, wx.LEFT | wx.RIGHT | wx.TOP, 5)
        viewing_sizer.Add(self.start_dir_picker, 0, wx.LEFT | wx.RIGHT | wx.TOP | wx.EXPAND, 5)

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
        viewing_sizer.Add(self.right_to_left_chk, 0, wx.LEFT | wx.RIGHT | wx.TOP, 5)
        viewing_sizer.Add(self.scroll_at_bottom_chk, 0, wx.LEFT | wx.RIGHT | wx.TOP, 5)
        viewing_sizer.Add(self.placeholder_autodelete_chk, 0, wx.LEFT | wx.RIGHT | wx.TOP, 5)
        viewing_sizer.Add(self.placeholder_single_chk, 0, wx.LEFT | wx.RIGHT | wx.TOP, 5)
        viewing_sizer.Add(self.placeholder_autoopen_chk, 0, wx.LEFT | wx.RIGHT | wx.TOP, 5)
        viewing_sizer.Add(self.placeholder_separate_chk, 0, wx.LEFT | wx.RIGHT | wx.TOP, 5)
        self.SetSizer(viewing_sizer)

    def on_fit_select(self, event: wx.CommandEvent):
        fit_type = event.GetClientData()
        self._update_custom_fit_display(fit_type)
        event.Skip()

    def on_ok(self, opt: Options):
        sel = self.fit_cbo.GetSelection()
        opt.fit_type = self.fit_cbo.GetClientData(sel)
        opt.fit_width_str = self.width_txt.GetValue()
        opt.start_dir = self.start_dir_picker.GetPath()
        opt.custom_bg = self.bg_color_custom_rdo.GetValue()
        opt.custom_bg_color = self.bg_color_picker.GetColour()

        opt.save_locally = self.settings_local_chk.GetValue()
        opt.real_fullscreen = self.real_fullscreen_chk.GetValue()
        opt.open_first = self.open_first_chk.GetValue()
        opt.auto_fullscreen = self.auto_fullscreen_chk.GetValue()
        opt.use_right_to_left = self.right_to_left_chk.GetValue()
        opt.scroll_at_bottom = self.scroll_at_bottom_chk.GetValue()
        opt.placeholder_delete = self.placeholder_autodelete_chk.GetValue()
        opt.placeholder_single = self.placeholder_single_chk.GetValue()
        opt.placeholder_autoopen = self.placeholder_autoopen_chk.GetValue()
        opt.placeholder_separate = self.placeholder_separate_chk.GetValue()
        opt.darkmode = self.dark_mode_system_rdo.GetSelection()

    def _update_custom_fit_display(self, fit_type: FitSettings.FitType):
        show = (fit_type == FitSettings.FitType.CUSTOM_WIDTH)
        self.width_label.Enable(show)
        self.width_txt.Enable(show)


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
