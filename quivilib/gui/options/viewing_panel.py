import wx

from quivilib.i18n import _
from quivilib.model import Settings
from quivilib.model.commandenum import FitSettings
from quivilib.model.options import ViewingOptions


class ViewingPanel(wx.Panel):
    def __init__(self, parent: wx.Window, settings: Settings, fit_choices: list[tuple[str, FitSettings.FitType]]):
        super().__init__(parent=parent, id=-1)
        self.fit_choices = fit_choices
        self.settings = settings

        self._init_viewing()

        self.__set_properties()
        self.__do_layout()

        self.Bind(wx.EVT_COMBOBOX, self.on_fit_select, self.fit_cbo)

    def _init_viewing(self):
        self.fit_label = wx.StaticText(self, -1, _("Fit"))
        self.fit_cbo = wx.ComboBox(self, -1, choices=[], style=wx.CB_DROPDOWN | wx.CB_READONLY)
        self.width_label = wx.StaticText(self, -1, _("Width"))
        self.width_txt = wx.TextCtrl(self, -1, "800")
        self.start_dir_lbl = wx.StaticText(self, -1, _("Start directory"))
        self.start_dir_picker = wx.DirPickerCtrl(self, -1)

        self.right_to_left_chk = wx.CheckBox(self, -1, _("View images right-to-left"))
        self.scroll_at_bottom_chk = wx.CheckBox(self, -1, _("Scroll horizontally when scrolling past end of image"))
        self.placeholder_autodelete_chk = wx.CheckBox(self, -1, _("Delete placeholders when opening"))
        self.placeholder_single_chk = wx.CheckBox(self, -1, _("Only allow a single placeholder"))
        self.placeholder_autoopen_chk = wx.CheckBox(self, -1, _("Automatically jump to placeholder page on open"))
        self.placeholder_separate_chk = wx.CheckBox(self, -1, _("Use separate menus for favorites and placeholders"))

    def __set_properties(self):
        """Initialize dialog checkboxes/dropdowns based on current application settings"""
        setting_fit_type = FitSettings.get_fittype(self.settings.get('Options', 'FitType'))
        for name, fit_type in self.fit_choices:
            idx = self.fit_cbo.Append(name, fit_type)
            if fit_type == setting_fit_type:
                self.fit_cbo.SetSelection(idx)
                self._update_custom_fit_display(fit_type)

        self.width_txt.SetValue(self.settings.get('Options', 'FitWidthCustomSize'))

        self.start_dir_picker.SetPath(self.settings.get('Options', 'StartDir'))

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

    def on_ok(self):
        opt = ViewingOptions
        sel = self.fit_cbo.GetSelection()
        opt.fit_type = self.fit_cbo.GetClientData(sel)
        opt.fit_width_str = self.width_txt.GetValue()
        opt.start_dir = self.start_dir_picker.GetPath()

        opt.use_right_to_left = self.right_to_left_chk.GetValue()
        opt.scroll_at_bottom = self.scroll_at_bottom_chk.GetValue()
        opt.placeholder_delete = self.placeholder_autodelete_chk.GetValue()
        opt.placeholder_single = self.placeholder_single_chk.GetValue()
        opt.placeholder_autoopen = self.placeholder_autoopen_chk.GetValue()
        opt.placeholder_separate = self.placeholder_separate_chk.GetValue()
        return opt

    def _update_custom_fit_display(self, fit_type: FitSettings.FitType):
        show = (fit_type == FitSettings.FitType.CUSTOM_WIDTH)
        self.width_label.Enable(show)
        self.width_txt.Enable(show)
