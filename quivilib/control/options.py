from pubsub import pub as Publisher

from quivilib.i18n import _
from quivilib.model import App
from quivilib.model.commandenum import FitSettings
from quivilib.model.options import Options


#TODO: (1,2) Improve: when setting start dir, check if it is a special folder
#    and if it is, save a reference (e.g. %DocumentsDir%) to it instead of the
#    hard coded path


_fit_choices = [
    (_("None"), FitSettings.FitType.NONE),
    (_("Width"), FitSettings.FitType.WIDTH),
    (_("Height"), FitSettings.FitType.HEIGHT),
    (_("Window"), FitSettings.FitType.WINDOW),
    (_("Width if larger"), FitSettings.FitType.WIDTH_IF_LARGER),
    (_("Height if larger"), FitSettings.FitType.HEIGHT_IF_LARGER),
    (_("Window if larger"), FitSettings.FitType.WINDOW_IF_LARGER),
    (_("Custom width"), FitSettings.FitType.CUSTOM_WIDTH),
    (_("Custom width if larger"), FitSettings.FitType.CUSTOM_WIDTH_IF_LARGER),
]
def get_fit_choices() -> list[tuple[str, FitSettings.FitType]]:
    return _fit_choices


class OptionsController(object):
    def __init__(self, control, model: App):
        self.control = control
        self.model = model
        Publisher.subscribe(self.on_update, 'options.update')
        
    def open_dialog(self):
        fit_choices = get_fit_choices()
        commands = self.control.menu.commands

        Publisher.sendMessage('options.open_dialog',
                                fit_choices=fit_choices, 
                                settings=self.model.settings, 
                                commands=commands,
                                languages=self.control.i18n.langs,
                                save_locally=self.control.use_local_config()
        )
        
    def on_update(self, *, opt: Options):
        #TODO: All of these value adjustments should be moved to the model instead.
        def to_int(val):
            if val is None:
                return 0
            try:
                return int(val)
            except ValueError:
                return 0

        fit_width = to_int(opt.viewing_options.fit_width_str)
        drag_threshold = to_int(opt.mouse_options.drag_threshold)
        hide_duration = to_int(opt.mouse_options.hide_mouse_duration)
        always_drag = '1' if opt.mouse_options.always_drag else '0'
        if fit_width <= 0:
            #I guess there's no need to bother the user with this, so just use default
            fit_width = self.model.settings.get_default('Options', 'FitWidthCustomSize')
            
        custom_bg = '1' if opt.general_options.custom_bg else '0'
        custom_bg_color = '%d,%d,%d' % (opt.general_options.custom_bg_color.Red(), opt.general_options.custom_bg_color.Green(), opt.general_options.custom_bg_color.Blue())
        real_fullscreen = '1' if opt.general_options.real_fullscreen else '0'
        auto_fullscreen = '1' if opt.general_options.auto_fullscreen else '0'
        use_right_to_left = '1' if opt.viewing_options.use_right_to_left else '0'
        scroll_at_bottom = '1' if opt.viewing_options.scroll_at_bottom else '0'
        placeholder_delete = '1' if opt.viewing_options.placeholder_delete else '0'
        placeholder_single = '1' if opt.viewing_options.placeholder_single else '0'
        placeholder_autoopen = '1' if opt.viewing_options.placeholder_autoopen else '0'
        placeholder_separate = '1' if opt.viewing_options.placeholder_separate else '0'

        open_first = '1' if opt.general_options.open_first else '0'
        self.model.settings.set('Options', 'FitType', str(opt.viewing_options.fit_type))
        self.model.settings.set('Options', 'FitWidthCustomSize', str(fit_width))
        self.model.settings.set('Options', 'StartDir', opt.viewing_options.start_dir)
        self.model.settings.set('Options', 'CustomBackgroundColor', custom_bg_color)
        self.model.settings.set('Options', 'CustomBackground', custom_bg)
        self.model.settings.set('Options', 'RealFullscreen', real_fullscreen)
        self.model.settings.set('Options', 'AutoFullscreen', auto_fullscreen)
        self.model.settings.set('Options', 'UseRightToLeft', use_right_to_left)
        self.model.settings.set('Options', 'HorizontalScrollAtBottom', scroll_at_bottom)
        self.model.settings.set('Options', 'PlaceholderDelete', placeholder_delete)
        self.model.settings.set('Options', 'PlaceholderSingle', placeholder_single)
        self.model.settings.set('Options', 'PlaceholderAutoOpen', placeholder_autoopen)
        self.model.settings.set('Options', 'PlaceholderSeparateMenu', placeholder_separate)
        self.model.settings.set('Options', 'OpenFirst', open_first)
        self.model.settings.set('Options', 'DarkMode', str(opt.general_options.darkmode))
        self.model.settings.set('Mouse', 'LeftClickCmd', str(int(opt.mouse_options.left_click_cmd)))
        self.model.settings.set('Mouse', 'MiddleClickCmd', str(int(opt.mouse_options.middle_click_cmd)))
        self.model.settings.set('Mouse', 'RightClickCmd', str(int(opt.mouse_options.right_click_cmd)))
        self.model.settings.set('Mouse', 'Aux1ClickCmd', str(int(opt.mouse_options.aux1_click_cmd)))
        self.model.settings.set('Mouse', 'Aux2ClickCmd', str(int(opt.mouse_options.aux2_click_cmd)))
        self.model.settings.set('Mouse', 'AlwaysLeftMouseDrag', always_drag)
        self.model.settings.set('Mouse', 'DragThreshold', str(drag_threshold))
        self.model.settings.set('Mouse', 'HideMouseDuration', str(hide_duration))

        self.control.i18n.language = opt.language
        self.control.menu.set_shortcuts(opt.shortcuts)
        self.control.set_settings_location(opt.general_options.save_locally)
