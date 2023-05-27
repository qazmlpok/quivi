from pubsub import pub as Publisher

from quivilib.i18n import _
from quivilib.model.settings import Settings

#TODO: (1,2) Improve: when setting start dir, check if it is a special folder
#    and if it is, save a reference (e.g. %DocumentsDir%) to it instead of the
#    hard coded path


def get_fit_choices():
    fit_choices = [(_("None"), Settings.FIT_NONE),
                       (_("Width"), Settings.FIT_WIDTH),
                       (_("Height"), Settings.FIT_HEIGHT),
                       (_("Window"), Settings.FIT_BOTH),
                       (_("Width if larger"), Settings.FIT_WIDTH_OVERSIZE),
                       (_("Height if larger"), Settings.FIT_HEIGHT_OVERSIZE),
                       (_("Window if larger"), Settings.FIT_BOTH_OVERSIZE),
                       (_("Custom width"), Settings.FIT_CUSTOM_WIDTH),
                       ]
    return fit_choices


class OptionsController(object):
    def __init__(self, control, model):
        self.control = control
        self.model = model
        Publisher.subscribe(self.on_update, 'options.update')
        
    def open_dialog(self):
        fit_choices = get_fit_choices()
        categories = self.control.menu.command_cats

        Publisher.sendMessage('options.open_dialog',
                                fit_choices=fit_choices, 
                                settings=self.model.settings, 
                                categories=categories,
                                available_languages=self.control.i18n.available_languages,
                                active_language=self.control.i18n.language,
                                save_locally=self.control.can_save_settings_locally()
        )
        
    def on_update(self, *, opt):
        try:
            fit_width = int(opt.fit_width_str)
        except ValueError:
            fit_width = None
        try:
            drag_threshold = int(opt.drag_threshold)
        except ValueError:
            drag_threshold = 0
        if fit_width is None or fit_width <= 0:
            #I guess there's no need to bother the user with this, so just use default
            fit_width = self.model.settings.get_default('Options', 'FitWidthCustomSize')
            
        custom_bg = '1' if opt.custom_bg else '0'
        custom_bg_color = '%d,%d,%d' % (opt.custom_bg_color.Red(), opt.custom_bg_color.Green(), opt.custom_bg_color.Blue())
        real_fullscreen = '1' if opt.real_fullscreen else '0'
        auto_fullscreen = '1' if opt.auto_fullscreen else '0'
        placeholder_delete = '1' if opt.placeholder_delete else '0'
        placeholder_single = '1' if opt.placeholder_single else '0'
        placeholder_autoopen = '1' if opt.placeholder_autoopen else '0'
        always_drag = '1' if opt.always_drag else '0'
        open_first = '1' if opt.open_first else '0'
        
        self.model.settings.set('Options', 'FitType', opt.fit_type)
        self.model.settings.set('Options', 'FitWidthCustomSize', fit_width)
        self.model.settings.set('Options', 'StartDir', opt.start_dir)
        self.model.settings.set('Options', 'CustomBackgroundColor', custom_bg_color)
        self.model.settings.set('Options', 'CustomBackground', custom_bg)
        self.model.settings.set('Options', 'RealFullscreen', real_fullscreen)
        self.model.settings.set('Options', 'AutoFullscreen', auto_fullscreen)
        self.model.settings.set('Options', 'PlaceholderDelete', placeholder_delete)
        self.model.settings.set('Options', 'PlaceholderSingle', placeholder_single)
        self.model.settings.set('Options', 'PlaceholderAutoOpen', placeholder_autoopen)
        self.model.settings.set('Options', 'OpenFirst', open_first)
        self.model.settings.set('Mouse', 'LeftClickCmd', opt.left_click_cmd)
        self.model.settings.set('Mouse', 'MiddleClickCmd', opt.middle_click_cmd)
        self.model.settings.set('Mouse', 'RightClickCmd', opt.right_click_cmd)
        self.model.settings.set('Mouse', 'Aux1ClickCmd', opt.aux1_click_cmd)
        self.model.settings.set('Mouse', 'Aux2ClickCmd', opt.aux2_click_cmd)
        self.model.settings.set('Mouse', 'AlwaysLeftMouseDrag', always_drag)
        self.model.settings.set('Mouse', 'DragThreshold', drag_threshold)
        self.control.i18n.language = opt.language
        self.control.menu.set_shortcuts(opt.shortcuts)
        self.control.set_settings_location(opt.save_locally)
