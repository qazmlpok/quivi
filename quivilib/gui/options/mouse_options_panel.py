import wx

from quivilib.i18n import _
from quivilib.model import Settings
from quivilib.model.command import Command
from quivilib.model.commandenum import CommandFlags
from quivilib.model.options import Options


class MouseOptionsPanel(wx.Panel):
    def __init__(self, parent: wx.Window, settings: Settings, commands: list[Command]):
        super().__init__(parent=parent, id=-1)

        self._init_mouse()

        self.set_mouse_cbo(commands)
        self.__set_properties(settings)
        self.__do_layout()

    def _init_mouse(self):
        def _make_mouse_cbo(text):
            lbl = wx.StaticText(self, -1, text)
            cbo = wx.ComboBox(self, -1, choices=[], style=wx.CB_DROPDOWN|wx.CB_READONLY)
            return (lbl, cbo)
        (self.mouse_left_lbl,self.mouse_left_cbo) = _make_mouse_cbo(_("Left click"))
        (self.mouse_middle_lbl,self.mouse_middle_cbo) = _make_mouse_cbo(_("Middle click"))
        (self.mouse_right_lbl,self.mouse_right_cbo) = _make_mouse_cbo(_("Right click"))
        (self.mouse_aux1_lbl,self.mouse_aux1_cbo) = _make_mouse_cbo(_("Aux1 click"))
        (self.mouse_aux2_lbl,self.mouse_aux2_cbo) = _make_mouse_cbo(_("Aux2 click"))
        self._mouse_cbos = (self.mouse_left_cbo, self.mouse_middle_cbo, self.mouse_right_cbo, self.mouse_aux1_cbo, self.mouse_aux2_cbo)
        
        #This looks worse than I hoped, but I think it's still better than nothing.
        self.mouse_separator = wx.StaticLine(self, size=wx.Size(100, 1), style=wx.LI_HORIZONTAL)
        
        self.always_drag_chk = wx.CheckBox(self, -1, _("Always drag image with left mouse"))
        self.threshold_lbl = wx.StaticText(self, -1, _("Threshold:"))    #TODO: Better text.
        self.pixels_lbl = wx.StaticText(self, -1, _("px"))
        self.threshold_txt = wx.TextCtrl(self, -1)
        #This doesn't return the size of the "padding" - and it changes on different platforms/themes.
        sz = self.threshold_txt.GetTextExtent('99')
        self.threshold_txt.SetInitialSize(wx.Size(sz.x+30, -1))

        self.hide_cursor_lbl = wx.StaticText(self, -1, _("Hide mouse cursor if not moved for"))
        self.hide_cursor_post_lbl = wx.StaticText(self, -1, _("seconds"))
        self.hide_cursor_txt = wx.TextCtrl(self, -1)
        self.hide_cursor_txt.SetInitialSize(wx.Size(sz.x + 30, -1))
        
    def set_mouse_cbo(self, commands: list[Command]):
        for m in self._mouse_cbos:
            m.Append(_("None"), -1)
        #Commands will be in the same order they are defined in MenuDefinitionList. Same-groups are inherently together.
        for cmd in commands:
            text = cmd.name_and_category
            if cmd.flags & CommandFlags.MOUSE:
                for m in self._mouse_cbos:
                    m.Append(text, cmd.ide)

    def __set_properties(self, settings: Settings):
        self._set_selected(self.mouse_left_cbo, settings.getint('Mouse', 'LeftClickCmd'))
        self._set_selected(self.mouse_middle_cbo, settings.getint('Mouse', 'MiddleClickCmd'))
        self._set_selected(self.mouse_right_cbo, settings.getint('Mouse', 'RightClickCmd'))
        self._set_selected(self.mouse_aux1_cbo, settings.getint('Mouse', 'Aux1ClickCmd'))
        self._set_selected(self.mouse_aux2_cbo, settings.getint('Mouse', 'Aux2ClickCmd'))
        always_drag = (settings.get('Mouse', 'AlwaysLeftMouseDrag') == '1')
        self.always_drag_chk.SetValue(always_drag)
        self.threshold_txt.SetValue(settings.get('Mouse', 'DragThreshold'))
        self.hide_cursor_txt.SetValue(settings.get('Mouse', 'HideMouseDuration'))

    def __do_layout(self):
        mouse_sizer = wx.BoxSizer(wx.VERTICAL)

        # Mouse bindings
        mouse_sizer.Add(self.mouse_left_lbl, 0, wx.LEFT | wx.RIGHT | wx.TOP, 5)
        mouse_sizer.Add(self.mouse_left_cbo, 0, wx.LEFT | wx.RIGHT | wx.TOP, 5)
        mouse_sizer.Add(self.mouse_middle_lbl, 0, wx.LEFT | wx.RIGHT | wx.TOP, 5)
        mouse_sizer.Add(self.mouse_middle_cbo, 0, wx.LEFT | wx.RIGHT | wx.TOP, 5)
        mouse_sizer.Add(self.mouse_right_lbl, 0, wx.LEFT | wx.RIGHT | wx.TOP, 5)
        mouse_sizer.Add(self.mouse_right_cbo, 0, wx.LEFT | wx.RIGHT | wx.TOP, 5)
        mouse_sizer.Add(self.mouse_aux1_lbl, 0, wx.LEFT | wx.RIGHT | wx.TOP, 5)
        mouse_sizer.Add(self.mouse_aux1_cbo, 0, wx.LEFT | wx.RIGHT | wx.TOP, 5)
        mouse_sizer.Add(self.mouse_aux2_lbl, 0, wx.LEFT | wx.RIGHT | wx.TOP, 5)
        mouse_sizer.Add(self.mouse_aux2_cbo, 0, wx.LEFT | wx.RIGHT | wx.TOP, 5)
        mouse_sizer.Add(self.mouse_separator, 0, wx.TOP | wx.EXPAND, 10)

        # Drag checkbox and treshold
        mouse_drag_sizer = wx.BoxSizer(wx.VERTICAL)
        mouse_drag_sizer_nested = wx.BoxSizer(wx.HORIZONTAL)
        mouse_drag_sizer.Add(self.always_drag_chk, 0, wx.LEFT | wx.TOP, 5)
        mouse_drag_sizer_nested.Add(self.threshold_lbl, 0, wx.LEFT | wx.RIGHT | wx.ALIGN_CENTER_VERTICAL, 5)
        mouse_drag_sizer_nested.Add(self.threshold_txt, 0, wx.LEFT | wx.RIGHT | wx.ALIGN_CENTER_VERTICAL, 5)
        mouse_drag_sizer_nested.Add(self.pixels_lbl, 0, wx.ALIGN_CENTER_VERTICAL, 5)
        mouse_drag_sizer.Add(mouse_drag_sizer_nested, 0, wx.ALIGN_RIGHT | wx.LEFT | wx.RIGHT | wx.TOP, 5)
        mouse_sizer.Add(mouse_drag_sizer, 0, wx.LEFT | wx.RIGHT | wx.TOP, 5)

        # Hide mouse
        mouse_hide_sizer = wx.BoxSizer(wx.HORIZONTAL)
        mouse_hide_sizer.Add(self.hide_cursor_lbl, 0, wx.LEFT | wx.RIGHT | wx.ALIGN_CENTER_VERTICAL, 5)
        mouse_hide_sizer.Add(self.hide_cursor_txt, 0, wx.LEFT | wx.RIGHT | wx.ALIGN_CENTER_VERTICAL, 5)
        mouse_hide_sizer.Add(self.hide_cursor_post_lbl, 0, wx.LEFT | wx.RIGHT | wx.ALIGN_CENTER_VERTICAL, 5)
        mouse_sizer.Add(mouse_hide_sizer, 0, wx.LEFT | wx.RIGHT | wx.TOP, 5)

        self.SetSizer(mouse_sizer)
        self.Layout()

    def on_ok(self, opt: Options):
        #TODO: Use a separate object. Options is also too big.
        sel = self.mouse_left_cbo.GetSelection()
        opt.left_click_cmd = self.mouse_left_cbo.GetClientData(sel)
        sel = self.mouse_middle_cbo.GetSelection()
        opt.middle_click_cmd = self.mouse_left_cbo.GetClientData(sel)
        sel = self.mouse_right_cbo.GetSelection()
        opt.right_click_cmd = self.mouse_left_cbo.GetClientData(sel)
        sel = self.mouse_aux1_cbo.GetSelection()
        opt.aux1_click_cmd = self.mouse_left_cbo.GetClientData(sel)
        sel = self.mouse_aux2_cbo.GetSelection()
        opt.aux2_click_cmd = self.mouse_left_cbo.GetClientData(sel)

        opt.always_drag = self.always_drag_chk.GetValue()
        opt.drag_threshold = self.threshold_txt.GetValue()
        opt.hide_mouse_duration = self.hide_cursor_txt.GetValue()

    @staticmethod
    def _set_selected(control: wx.ComboBox, item):
        for i in range(control.GetCount()):
            if control.GetClientData(i) == item:
                control.SetSelection(i)
                break
