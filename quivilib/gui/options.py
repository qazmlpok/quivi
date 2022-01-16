

#TODO: (2,2) Improve: change the command listbox into a listctrl with columns:
#    (Category / Command / Assigned shortcuts)

from quivilib.i18n import _
from quivilib.model.shortcut import Shortcut
from quivilib.model.settings import Settings
import quivilib.gui.hotkeyctrl as hk
from quivilib.model.options import Options

import wx
from pubsub import pub as Publisher
from wx.lib import langlistctrl


class OptionsDialog(wx.Dialog):
    def __init__(self, parent, fit_choices, settings, categories,
                 available_languages, active_language, save_locally):
        self.fit_choices = fit_choices
        self.save_locally = save_locally
        self.settings = settings
        self.commands = []
        self.categories = categories
        for category in categories:
            self.commands += category.commands
        # begin wxGlade: OptionsDialog.__init__
        wx.Dialog.__init__(self, parent=parent, style=wx.DEFAULT_DIALOG_STYLE|wx.RESIZE_BORDER)
        self.main_notebook = wx.Notebook(self, -1, style=0)
        self.mouse_pane = wx.Panel(self.main_notebook, -1)
        self.language_pane = wx.Panel(self.main_notebook, -1)
        self.keys_pane = wx.Panel(self.main_notebook, -1)
        self.viewing_pane = wx.Panel(self.main_notebook, -1)
        self.bg_color_sizer_staticbox = wx.StaticBox(self.viewing_pane, -1, _("Background color"))
        self.fit_label = wx.StaticText(self.viewing_pane, -1, _("Fit"))
        self.fit_cbo = wx.ComboBox(self.viewing_pane, -1, choices=[], style=wx.CB_DROPDOWN|wx.CB_READONLY)
        self.width_label = wx.StaticText(self.viewing_pane, -1, _("Width"))
        self.width_txt = wx.TextCtrl(self.viewing_pane, -1, "800")
        self.start_dir_lbl = wx.StaticText(self.viewing_pane, -1, _("Start directory"))
        self.start_dir_picker = wx.DirPickerCtrl(self.viewing_pane, -1)
        self.bg_color_default_rdo = wx.RadioButton(self.viewing_pane, -1, _("Default system color"), style=wx.RB_GROUP)
        self.bg_color_custom_rdo = wx.RadioButton(self.viewing_pane, -1, _("Custom color:"))
        self.bg_color_picker = wx.ColourPickerCtrl(self.viewing_pane, -1)
        self.real_fullscreen_chk = wx.CheckBox(self.viewing_pane, -1, _("Hide menu and status on full screen"))
        self.open_first_chk = wx.CheckBox(self.viewing_pane, -1, _("Open first image of the folder automatically"))
        self.settings_local_chk = wx.CheckBox(self.viewing_pane, -1, _("Portable mode (save settings inside the program folder)"))
        self.commands_label = wx.StaticText(self.keys_pane, -1, _("Commands"))
        self.commands_lst = wx.ListBox(self.keys_pane, -1, choices=[])
        self.shortcuts_lbl = wx.StaticText(self.keys_pane, -1, _("Shortcuts for selected command"))
        self.shorcuts_cbo = wx.ComboBox(self.keys_pane, -1, choices=[], style=wx.CB_DROPDOWN|wx.CB_READONLY|wx.CB_SORT)
        self.shortcut_remove_btn = wx.Button(self.keys_pane, -1, _("Remove"))
        self.new_shortcut_lbl = wx.StaticText(self.keys_pane, -1, _("New shortcut"))
        self.new_shortcut_key = hk.HotkeyCtrl(self.keys_pane, -1, _("Press key"))
        self.shortcut_assign_btn = wx.Button(self.keys_pane, -1, _("Assign"))
        self.assigned_comamnd_lbl = wx.StaticText(self.keys_pane, -1, "")
        self.reset_btn = wx.Button(self.keys_pane, -1, _("Reset all to defaults"))
        self.lang_lst = langlistctrl.LanguageListCtrl(self.language_pane, -1, style=wx.LC_LIST|wx.LC_NO_HEADER, filter=langlistctrl.LC_ONLY, only=available_languages, select=active_language)
        self.mouse_left_lbl = wx.StaticText(self.mouse_pane, -1, _("Left click"))
        self.mouse_left_cbo = wx.ComboBox(self.mouse_pane, -1, choices=[], style=wx.CB_DROPDOWN|wx.CB_DROPDOWN|wx.CB_READONLY|wx.CB_SORT)
        self.mouse_middle_lbl = wx.StaticText(self.mouse_pane, -1, _("Middle click"))
        self.mouse_middle_cbo = wx.ComboBox(self.mouse_pane, -1, choices=[], style=wx.CB_DROPDOWN|wx.CB_DROPDOWN|wx.CB_READONLY|wx.CB_SORT)
        self.mouse_right_lbl = wx.StaticText(self.mouse_pane, -1, _("Right click"))
        self.mouse_right_cbo = wx.ComboBox(self.mouse_pane, -1, choices=[], style=wx.CB_DROPDOWN|wx.CB_DROPDOWN|wx.CB_READONLY|wx.CB_SORT)
        self.ok_button = wx.Button(self, wx.ID_OK, _("&OK"))
        self.cancel_button = wx.Button(self, wx.ID_CANCEL, _("&Cancel"))

        self.__set_properties()
        self.__do_layout()

        self.Bind(wx.EVT_COMBOBOX, self.on_fit_select, self.fit_cbo)
        self.Bind(wx.EVT_LISTBOX, self.on_command_select, self.commands_lst)
        self.Bind(wx.EVT_BUTTON, self.on_remove_shorcut, self.shortcut_remove_btn)
        self.Bind(wx.EVT_BUTTON, self.on_assign_shortcut, self.shortcut_assign_btn)
        self.Bind(wx.EVT_BUTTON, self.on_reset_all, self.reset_btn)
        self.Bind(wx.EVT_BUTTON, self.on_ok, self.ok_button)
        self.Bind(wx.EVT_BUTTON, self.on_cancel, self.cancel_button)
        self.Bind(hk.EVT_HOTKEY, self.on_hotkey_pressed, self.new_shortcut_key)
        # end wxGlade
        
        self.lang_lst.SetColumnWidth(0, self.lang_lst.GetClientSize()[0])
        
        self.shortcuts = {}
        for cmd in self.commands:
            if cmd is not None:
                self.shortcuts[cmd] = cmd.shortcuts[:]

    def __set_properties(self):
        # begin wxGlade: OptionsDialog.__set_properties
        self.SetTitle(_("Options"))
        self.SetSize((400, 400))
        self.fit_cbo.SetSelection(-1)
        # end wxGlade
        
        for category in self.categories:
            for cmd in category.commands:
                if cmd is None:
                    continue
                text = '%s | %s' % (category.clean_name, cmd.clean_name)
                self.commands_lst.Append(text, cmd)
                self.mouse_left_cbo.Append(text, cmd.ide)
                self.mouse_middle_cbo.Append(text, cmd.ide)
                self.mouse_right_cbo.Append(text, cmd.ide)
        
        self._set_selected(self.mouse_left_cbo, self.settings.getint('Mouse', 'LeftClickCmd'))
        self._set_selected(self.mouse_middle_cbo, self.settings.getint('Mouse', 'MiddleClickCmd'))
        self._set_selected(self.mouse_right_cbo, self.settings.getint('Mouse', 'RightClickCmd'))
                
        for name, fit_type in self.fit_choices:
            idx = self.fit_cbo.Append(name, fit_type)
            if fit_type == self.settings.getint('Options', 'FitType'):
                self.fit_cbo.SetSelection(idx)
                self._update_custom_fit_display(fit_type)
                
        self.width_txt.SetValue(self.settings.get('Options', 'FitWidthCustomSize'))
                
        self.start_dir_picker.SetTextCtrlProportion(1)
        self.start_dir_picker.SetPath(self.settings.get('Options', 'StartDir'))
        
        if self.settings.get('Options', 'CustomBackground') == '1':
            self.bg_color_custom_rdo.SetValue(True)
        else:
            self.bg_color_default_rdo.SetValue(True)
        color = self.settings.get('Options', 'CustomBackgroundColor').split(',')
        color = wx.Colour(*[int(c) for c in color])
        self.bg_color_picker.SetColour(color)
        
        real_fullscreen = (self.settings.get('Options', 'RealFullscreen') == '1')
        self.real_fullscreen_chk.SetValue(real_fullscreen)
        open_first = (self.settings.get('Options', 'OpenFirst') == '1')
        self.open_first_chk.SetValue(open_first)
        self.settings_local_chk.SetValue(self.save_locally)
        
        self.ok_button.SetDefault()

    def __do_layout(self):
        # begin wxGlade: OptionsDialog.__do_layout
        main_sizer = wx.BoxSizer(wx.VERTICAL)
        btn_sizer = wx.StdDialogButtonSizer()
        mouse_sizer = wx.BoxSizer(wx.VERTICAL)
        language_sizer = wx.BoxSizer(wx.VERTICAL)
        keys_sizer = wx.BoxSizer(wx.VERTICAL)
        new_shortcut_sizer = wx.BoxSizer(wx.HORIZONTAL)
        shortcuts_sizer = wx.BoxSizer(wx.HORIZONTAL)
        viewing_sizer = wx.BoxSizer(wx.VERTICAL)
        bg_color_sizer = wx.StaticBoxSizer(self.bg_color_sizer_staticbox, wx.VERTICAL)
        custom_bg_color_sizer = wx.BoxSizer(wx.HORIZONTAL)
        viewing_sizer.Add(self.fit_label, 0, wx.LEFT|wx.RIGHT|wx.TOP, 5)
        viewing_sizer.Add(self.fit_cbo, 0, wx.LEFT|wx.RIGHT|wx.TOP, 5)
        viewing_sizer.Add(self.width_label, 0, wx.LEFT|wx.RIGHT|wx.TOP, 5)
        viewing_sizer.Add(self.width_txt, 0, wx.LEFT|wx.RIGHT|wx.TOP, 5)
        viewing_sizer.Add(self.start_dir_lbl, 0, wx.LEFT|wx.RIGHT|wx.TOP, 5)
        viewing_sizer.Add(self.start_dir_picker, 0, wx.LEFT|wx.RIGHT|wx.TOP|wx.EXPAND, 5)
        bg_color_sizer.Add(self.bg_color_default_rdo, 0, wx.LEFT|wx.RIGHT|wx.TOP, 5)
        custom_bg_color_sizer.Add(self.bg_color_custom_rdo, 0, wx.ALIGN_CENTER_VERTICAL, 0)
        custom_bg_color_sizer.Add(self.bg_color_picker, 0, wx.LEFT|wx.RIGHT|wx.EXPAND, 5)
        bg_color_sizer.Add(custom_bg_color_sizer, 1, wx.ALL|wx.EXPAND, 5)
        viewing_sizer.Add(bg_color_sizer, 0, wx.LEFT|wx.RIGHT|wx.TOP|wx.EXPAND, 5)
        viewing_sizer.Add(self.real_fullscreen_chk, 0, wx.LEFT|wx.RIGHT|wx.TOP, 5)
        viewing_sizer.Add(self.open_first_chk, 0, wx.LEFT|wx.RIGHT|wx.TOP, 5)
        viewing_sizer.Add(self.settings_local_chk, 0, wx.ALL, 5)
        self.viewing_pane.SetSizer(viewing_sizer)
        keys_sizer.Add(self.commands_label, 0, wx.LEFT|wx.RIGHT|wx.TOP, 5)
        keys_sizer.Add(self.commands_lst, 1, wx.LEFT|wx.RIGHT|wx.TOP|wx.EXPAND, 5)
        keys_sizer.Add(self.shortcuts_lbl, 0, wx.LEFT|wx.RIGHT|wx.TOP, 5)
        shortcuts_sizer.Add(self.shorcuts_cbo, 1, wx.RIGHT, 5)
        shortcuts_sizer.Add(self.shortcut_remove_btn, 0, 0, 0)
        keys_sizer.Add(shortcuts_sizer, 0, wx.LEFT|wx.RIGHT|wx.TOP|wx.EXPAND, 5)
        keys_sizer.Add(self.new_shortcut_lbl, 0, wx.LEFT|wx.RIGHT|wx.TOP, 5)
        new_shortcut_sizer.Add(self.new_shortcut_key, 1, wx.RIGHT|wx.EXPAND, 5)
        new_shortcut_sizer.Add(self.shortcut_assign_btn, 0, 0, 0)
        keys_sizer.Add(new_shortcut_sizer, 0, wx.LEFT|wx.RIGHT|wx.TOP|wx.EXPAND, 5)
        keys_sizer.Add(self.assigned_comamnd_lbl, 0, wx.LEFT|wx.RIGHT|wx.TOP|wx.EXPAND, 5)
        keys_sizer.Add(self.reset_btn, 0, wx.ALL, 5)
        self.keys_pane.SetSizer(keys_sizer)
        language_sizer.Add(self.lang_lst, 1, wx.ALL|wx.EXPAND, 5)
        self.language_pane.SetSizer(language_sizer)
        mouse_sizer.Add(self.mouse_left_lbl, 0, wx.LEFT|wx.RIGHT|wx.TOP, 5)
        mouse_sizer.Add(self.mouse_left_cbo, 0, wx.LEFT|wx.RIGHT|wx.TOP, 5)
        mouse_sizer.Add(self.mouse_middle_lbl, 0, wx.LEFT|wx.RIGHT|wx.TOP, 5)
        mouse_sizer.Add(self.mouse_middle_cbo, 0, wx.LEFT|wx.RIGHT|wx.TOP, 5)
        mouse_sizer.Add(self.mouse_right_lbl, 0, wx.LEFT|wx.RIGHT|wx.TOP, 5)
        mouse_sizer.Add(self.mouse_right_cbo, 0, wx.LEFT|wx.RIGHT|wx.TOP, 5)
        self.mouse_pane.SetSizer(mouse_sizer)
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

    def on_fit_select(self, event): # wxGlade: OptionsDialog.<event_handler>
        fit_type = event.GetClientData()
        self._update_custom_fit_display(fit_type)
        event.Skip()

    def on_command_select(self, event): # wxGlade: OptionsDialog.<event_handler>
        cmd = event.GetClientData()
        self._load_shortcuts(cmd)
        event.Skip()

    def on_remove_shorcut(self, event): # wxGlade: OptionsDialog.<event_handler>
        sel = self.shorcuts_cbo.GetSelection()
        if sel != -1:
            shortcut = self.shorcuts_cbo.GetClientData(sel)
            cmd = self.commands_lst.GetClientData(self.commands_lst.GetSelection())
            self.shortcuts[cmd].remove(shortcut)
            self._load_shortcuts(cmd)
        event.Skip()

    def on_assign_shortcut(self, event): # wxGlade: OptionsDialog.<event_handler>
        sel = self.commands_lst.GetSelection()
        if sel != -1 and self.new_shortcut_key.IsOk():
            cmd = self.commands_lst.GetClientData(sel)
            shortcut = Shortcut(self.new_shortcut_key.GetAcceleratorFlags(),
                                self.new_shortcut_key.GetKeyCode())
            for icmd in self.shortcuts:
                try:
                    self.shortcuts[icmd].remove(shortcut)
                except ValueError:
                    #Not in list
                    pass
            self.shortcuts[cmd].append(shortcut)
            self._load_shortcuts(cmd, shortcut)
            self.assigned_comamnd_lbl.SetLabel('')
            self.new_shortcut_key.Clear()
        event.Skip()

    def on_reset_all(self, event): # wxGlade: OptionsDialog.<event_handler>
        self.shortcuts = {}
        for cmd in self.commands:
            if cmd.default_shortcuts:
                self.shortcuts[cmd] = [cmd.default_shortcuts]
            else:
                self.shortcuts[cmd] = []
        sel = self.commands_lst.GetSelection()
        if sel != -1:
            cmd = self.commands_lst.GetClientData(sel)
            self._load_shortcuts(cmd)
        event.Skip()

    def on_ok(self, event): # wxGlade: OptionsDialog.<event_handler>
        opt = Options()
        sel = self.fit_cbo.GetSelection()
        opt.fit_type = self.fit_cbo.GetClientData(sel)
        opt.fit_width_str = self.width_txt.GetValue()
        opt.start_dir = self.start_dir_picker.GetPath()
        opt.custom_bg = self.bg_color_custom_rdo.GetValue()
        opt.custom_bg_color = self.bg_color_picker.GetColour()
        opt.language = self.lang_lst.GetLanguage()
        sel = self.mouse_left_cbo.GetSelection()
        opt.left_click_cmd = self.mouse_left_cbo.GetClientData(sel)
        sel = self.mouse_middle_cbo.GetSelection()
        opt.middle_click_cmd = self.mouse_left_cbo.GetClientData(sel)
        sel = self.mouse_right_cbo.GetSelection()
        opt.right_click_cmd = self.mouse_left_cbo.GetClientData(sel)
        opt.save_locally = self.settings_local_chk.GetValue()
        opt.real_fullscreen = self.real_fullscreen_chk.GetValue()
        opt.open_first = self.open_first_chk.GetValue()
        opt.shortcuts = self.shortcuts
        #TODO: (2,2) Improve: handle errors here
        Publisher.sendMessage('options.update', opt=opt)
        event.Skip()

    def on_cancel(self, event): # wxGlade: OptionsDialog.<event_handler>
        event.Skip()
        
    def on_hotkey_pressed(self, event):
        new_shortcut = Shortcut(event.GetAcceleratorFlags(), event.GetKeyCode())
        self.assigned_comamnd_lbl.SetLabel('')
        sel_cmd = self._get_selected_command()
        for cmd, shortcut_lst in list(self.shortcuts.items()):
            for shortcut in shortcut_lst:
                if new_shortcut == shortcut and cmd is not sel_cmd:
                    text = _('Assigned for "%s"') % (cmd.name)
                    self.assigned_comamnd_lbl.SetLabel(text)
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
            
    def _update_custom_fit_display(self, fit_type):
        show = (fit_type == Settings.FIT_CUSTOM_WIDTH)
        self.width_label.Enable(show)
        self.width_txt.Enable(show)
    
    @staticmethod
    def _set_selected(control, item):
        for i in range(control.GetCount()):
            if control.GetClientData(i) == item:
                control.SetSelection(i)
                break

# end of class OptionsDialog


if __name__ == '__main__':
    app = wx.App(False)
    dlg = OptionsDialog(None)
    dlg.ShowModal()