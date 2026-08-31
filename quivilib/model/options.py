import wx

from quivilib.model.commandenum import CommandName


class GeneralOptions:
    custom_bg: bool
    custom_bg_color: wx.Colour
    save_locally: bool
    auto_fullscreen: bool
    darkmode: int
    real_fullscreen: bool
    open_first: bool

class ViewingOptions:
    use_right_to_left: bool
    scroll_at_bottom: bool
    placeholder_delete: bool
    placeholder_single: bool
    placeholder_autoopen: bool
    placeholder_separate: bool
    fit_type: int
    fit_width_str: str
    start_dir: str

class MouseOptions:
    left_click_cmd: CommandName
    left_click_cmd: CommandName
    middle_click_cmd: CommandName
    right_click_cmd: CommandName
    aux1_click_cmd: CommandName
    aux2_click_cmd: CommandName
    always_drag: bool
    drag_threshold: str
    hide_mouse_duration: str


class Options():
    general_options: GeneralOptions
    viewing_options: ViewingOptions
    mouse_options: MouseOptions
    def __init__(self):
        #Keys tab
        self.shortcuts = None
        #Language tab
        self.language = None
