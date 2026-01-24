import wx.core

from quivilib.model.commandenum import CommandName


class Options():
    def __init__(self):
        self.shortcuts = None
        self.fit_type = None
        self.fit_width_str = None
        self.start_dir = None
        self.language = None
        # Mouse
        self.left_click_cmd: CommandName | None = None
        self.middle_click_cmd: CommandName | None = None
        self.right_click_cmd: CommandName | None = None
        self.aux1_click_cmd: CommandName | None = None
        self.aux2_click_cmd: CommandName | None = None
        self.always_drag: bool | None = None
        self.drag_threshold: str | None = None
        self.custom_bg: bool | None = None
        self.custom_bg_color: wx.core.Colour | None = None
        # Viewing checkboxes
        self.real_fullscreen: bool | None = None
        self.open_first: bool | None = None
        self.save_locally: bool | None = None
        self.auto_fullscreen: bool | None = None
        self.use_right_to_left: bool | None = None
        self.scroll_at_bottom: bool | None = None
        self.placeholder_delete: bool | None = None
        self.placeholder_single: bool | None = None
        self.placeholder_autoopen: bool | None = None
        self.placeholder_separate: bool | None = None
