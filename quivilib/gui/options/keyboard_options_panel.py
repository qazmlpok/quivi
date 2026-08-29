import wx

import quivilib.gui.hotkeyctrl as hk
from quivilib.i18n import _
from quivilib.model import Settings
from quivilib.model.command import Command
from quivilib.model.commandenum import CommandFlags
from quivilib.model.options import Options
from quivilib.model.shortcut import Shortcut


class KeyboardOptionsPanel(wx.Panel):
    def __init__(self, parent: wx.Window, settings: Settings, commands: list[Command]):
        super().__init__(parent=parent, id=-1)

        self.settings = settings
        self.commands = commands

        self._init_commands()

        self.__set_properties()
        self.__do_layout()

        self.Bind(wx.EVT_LISTBOX, self.on_command_select, self.commands_lst)
        self.Bind(wx.EVT_BUTTON, self.on_remove_shorcut, self.shortcut_remove_btn)
        self.Bind(wx.EVT_BUTTON, self.on_assign_shortcut, self.shortcut_assign_btn)
        self.Bind(wx.EVT_BUTTON, self.on_reset_all, self.reset_btn)
        self.Bind(hk.EVT_HOTKEY, self.on_hotkey_pressed, self.new_shortcut_key)

        self.shortcuts: dict[Command, list[Shortcut]] = {}
        for cmd in self.commands:
            if cmd is not None:
                self.shortcuts[cmd] = cmd.shortcuts[:]

    def _init_commands(self):
        self.commands_label = wx.StaticText(self, -1, _("Commands"))
        self.commands_lst = wx.ListBox(self, -1, choices=[])
        self.shortcuts_lbl = wx.StaticText(self, -1, _("Shortcuts for selected command"))
        self.shorcuts_cbo = wx.ComboBox(self, -1, choices=[], style=wx.CB_DROPDOWN | wx.CB_READONLY | wx.CB_SORT)
        self.shortcut_remove_btn = wx.Button(self, -1, _("Remove"))
        self.new_shortcut_lbl = wx.StaticText(self, -1, _("New shortcut"))
        self.new_shortcut_key = hk.HotkeyCtrl(self, -1, _("Press key"))
        self.shortcut_assign_btn = wx.Button(self, -1, _("Assign"))
        self.assigned_command_lbl = wx.StaticText(self, -1, "")
        self.reset_btn = wx.Button(self, -1, _("Reset all to defaults"))

    def __set_properties(self):
        # Commands will be in the same order they are defined in MenuDefinitionList. Same-groups are inherently together.
        for cmd in self.commands:
            text = cmd.name_and_category
            if cmd.flags & CommandFlags.KB:
                self.commands_lst.Append(text, cmd)

    def __do_layout(self):
        keys_sizer = wx.BoxSizer(wx.VERTICAL)
        shortcuts_sizer = wx.BoxSizer(wx.HORIZONTAL)
        new_shortcut_sizer = wx.BoxSizer(wx.HORIZONTAL)
        keys_sizer.Add(self.commands_label, 0, wx.LEFT | wx.RIGHT | wx.TOP, 5)
        keys_sizer.Add(self.commands_lst, 1, wx.LEFT | wx.RIGHT | wx.TOP | wx.EXPAND, 5)
        keys_sizer.Add(self.shortcuts_lbl, 0, wx.LEFT | wx.RIGHT | wx.TOP, 5)
        shortcuts_sizer.Add(self.shorcuts_cbo, 1, wx.RIGHT, 5)
        shortcuts_sizer.Add(self.shortcut_remove_btn, 0, 0, 0)
        keys_sizer.Add(shortcuts_sizer, 0, wx.LEFT | wx.RIGHT | wx.TOP | wx.EXPAND, 5)
        keys_sizer.Add(self.new_shortcut_lbl, 0, wx.LEFT | wx.RIGHT | wx.TOP, 5)
        new_shortcut_sizer.Add(self.new_shortcut_key, 1, wx.RIGHT | wx.EXPAND, 5)
        new_shortcut_sizer.Add(self.shortcut_assign_btn, 0, 0, 0)
        keys_sizer.Add(new_shortcut_sizer, 0, wx.LEFT | wx.RIGHT | wx.TOP | wx.EXPAND, 5)
        keys_sizer.Add(self.assigned_command_lbl, 0, wx.LEFT | wx.RIGHT | wx.TOP | wx.EXPAND, 5)
        keys_sizer.Add(self.reset_btn, 0, wx.ALL, 5)
        self.SetSizer(keys_sizer)

    def on_command_select(self, event: wx.CommandEvent):
        cmd = event.GetClientData()
        self._load_shortcuts(cmd)
        event.Skip()

    def on_remove_shorcut(self, event: wx.CommandEvent):
        sel = self.shorcuts_cbo.GetSelection()
        if sel != -1:
            shortcut = self.shorcuts_cbo.GetClientData(sel)
            cmd = self.commands_lst.GetClientData(self.commands_lst.GetSelection())
            self.shortcuts[cmd].remove(shortcut)
            self._load_shortcuts(cmd)
        event.Skip()

    def on_assign_shortcut(self, event: wx.CommandEvent):
        sel = self.commands_lst.GetSelection()
        if sel != -1 and self.new_shortcut_key.IsOk():
            cmd = self.commands_lst.GetClientData(sel)
            shortcut = Shortcut(self.new_shortcut_key.GetAcceleratorFlags(),
                                self.new_shortcut_key.GetKeyCode())
            for icmd in self.shortcuts:
                try:
                    self.shortcuts[icmd].remove(shortcut)
                except ValueError:
                    # Not in list
                    pass
            self.shortcuts[cmd].append(shortcut)
            self._load_shortcuts(cmd, shortcut)
            self.assigned_command_lbl.SetLabel('')
            self.new_shortcut_key.Clear()
        event.Skip()

    def on_reset_all(self, event: wx.CommandEvent):
        self.shortcuts = {}
        for cmd in self.commands:
            if cmd.default_shortcuts:
                self.shortcuts[cmd] = cmd.default_shortcuts[:]
            else:
                self.shortcuts[cmd] = []
        sel = self.commands_lst.GetSelection()
        if sel != -1:
            cmd = self.commands_lst.GetClientData(sel)
            self._load_shortcuts(cmd)
        event.Skip()

    def on_ok(self, opt: Options):
        opt.shortcuts = self.shortcuts

    def on_hotkey_pressed(self, event: hk.HotkeyUpdatedEvent):
        new_shortcut = Shortcut(event.GetAcceleratorFlags(), event.GetKeyCode())
        self.assigned_command_lbl.SetLabel('')
        sel_cmd = self._get_selected_command()
        for cmd, shortcut_lst in list(self.shortcuts.items()):
            for shortcut in shortcut_lst:
                if new_shortcut == shortcut and cmd is not sel_cmd:
                    text = _('Already Assigned to "%s"') % (cmd.name)
                    self.assigned_command_lbl.SetLabel(text)
                    return

    def _get_selected_command(self):
        sel = self.commands_lst.GetSelection()
        if sel >= 0:
            return self.commands_lst.GetClientData(sel)
        else:
            return None

    def _load_shortcuts(self, cmd, selected_shortcut=None):
        self.shorcuts_cbo.Clear()
        for shortcut in self.shortcuts[cmd]:
            self.shorcuts_cbo.Append(shortcut.name, shortcut)
        if self.shorcuts_cbo.GetCount() > 0:
            self.shorcuts_cbo.SetSelection(0)
        self._set_selected(self.shorcuts_cbo, selected_shortcut)

    @staticmethod
    def _set_selected(control: wx.ComboBox, item):
        for i in range(control.GetCount()):
            if control.GetClientData(i) == item:
                control.SetSelection(i)
                break
