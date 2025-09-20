#TODO: (2,3) Refactor: this module and classes were poorly named.
#    this is actually about commands, and not the menu.
from functools import partial

import wx
from pubsub import pub as Publisher

from quivilib.i18n import _
from quivilib.model.command import CommandName, Command, CommandCategory, CommandDefinitionList
from quivilib.model.shortcut import Shortcut
from quivilib.control import canvas
from quivilib.control.canvas import MovementType
from quivilib.model.settings import Settings

SHORTCUTS_KEY = 'Shortcuts'


class MenuController(object):
    def __init__(self, control, settings):
        self.settings = settings
        self.control = control
        self.commands = []
        self.command_definitions = CommandDefinitionList()
        self.main_menu, self.command_cats, self.commands = self._make_commands(self.control)
        self.main_menu_dict = {x.idx: x for x in self.main_menu}
        self._load_shortcuts(self.settings, self.commands)
        self.shortcuts = self._get_accelerator_table(self.commands)
        #These must be sent in this order
        Publisher.sendMessage('menu.built', main_menu=self.main_menu, commands=self.commands)
        Publisher.sendMessage('toolbar.built', commands=self._get_toolbar_commands(self.commands))
        #TODO: (2,2) Refactor: change this message name. This also notifies that
        #    shortcuts have changed.
        Publisher.sendMessage('menu.labels.changed', 
                                main_menu=self.main_menu, 
                                commands=self.commands, 
                                accel_table=self.shortcuts
        )
        
        Publisher.subscribe(self.on_language_changed, 'language.changed')
        Publisher.subscribe(self.on_command_execute, 'command.execute')
        #TODO: Better name; for function and message.
        #This is for a (mouse) command with two events; key down and key release.
        Publisher.subscribe(self.on_command_down_execute, 'command.down_execute')
        
    def set_shortcuts(self, shortcuts_dic):
        """Set new shortcuts.
        
        @type shortcuts_dic: dict(Command -> list(Shortcut))
        """
        for cmd, shortcuts in list(shortcuts_dic.items()):
            cmd.shortcuts = shortcuts
        self._save_shortcuts(self.settings, self.commands)
        self.shortcuts = self._get_accelerator_table(self.commands)
        Publisher.sendMessage('menu.labels.changed', 
                                main_menu=self.main_menu,
                                commands=self.commands,
                                accel_table=self.shortcuts
        )
        
    def on_language_changed(self):
        self._make_commands(self.control, True)
        Publisher.sendMessage('menu.labels.changed', 
                                main_menu=self.main_menu,
                                commands=self.commands,
                                accel_table=self.shortcuts
        )
        Publisher.sendMessage('toolbar.labels.changed', commands=self._get_toolbar_commands(self.commands))
        
    def on_command_execute(self, *, ide):
        [cmd() for cmd in self.commands if cmd.ide == ide]
    def on_command_down_execute(self, *, ide):
        [cmd.on_down() for cmd in self.commands if cmd.ide == ide]

    def _make_commands(self, control, update=False):
        """Make (or update) all commands.
        
        @param control: reference to the main controller instance
        @update: if True, then it will only update the existing commands.
            (Which will retranslate them when changing languages)
        """
        #TODO: (1,2) Refactor: does two different things 
        commands = []
        if update:
            cmd_dict = dict((cmd.ide, cmd) for cmd in self.commands)
            def make(ide, function, **kwparams):
                definition = self.command_definitions.commands[ide]
                cmd_dict[ide].update_translation(definition)
                return None
            
            def make_category(*params):
                idx, name = params[1:3]
                if idx in self.main_menu_dict:
                    category = self.main_menu_dict[idx]
                    category.name = name
                return None
        else:
            def make(ide, function, **kwparams):
                definition = self.command_definitions.commands[ide]
                command = Command(definition, function, **kwparams)
                commands.append(command)
                return command
            
            def make_category(*params):
                category = CommandCategory(*params)
                return category
        
        file_menu = (
         make(11001, 
              control.wallpaper.open_dialog,
              update_function=control.on_update_image_available_menu_item),
         make(11002, 
              control.copy_to_clipboard,
              update_function=control.on_update_image_available_menu_item),
         make(11005, 
              control.copy_path_to_clipboard,
              update_function=control.on_update_image_available_menu_item),
         make(11004, 
              control.delete,
              update_function=control.file_list.on_update_delete_menu_item),
         make(11006, 
              control.open_move_dialog,
              update_function=control.file_list.on_update_move_menu_item),
         None,
         make(11003, 
              control.options.open_dialog),
         None,
         make(wx.ID_EXIT, 
              control.quit)
        )
        folder_menu = (
         make(12001, 
              partial(control.file_list.select_next, 1)),
         make(12002, 
              partial(control.file_list.select_next, -1)),
         make(12003, 
              control.file_list.open_selected_container),
         make(12004, 
              control.file_list.open_parent),
         make(12005, 
              partial(control.file_list.open_sibling, 1)),
         make(12006, 
              partial(control.file_list.open_sibling, -1)),
         make(12007, 
              control.file_list.refresh),
         make(12008, 
              control.file_list.open_directory)
        )
        view_menu = (
         make(13001, 
              control.canvas.zoom_in,
              update_function=control.on_update_image_available_menu_item),
         make(13002, 
              control.canvas.zoom_out,
              update_function=control.on_update_image_available_menu_item),
         #TODO: Add mouse-specific version that zooms in on mouse position. Also give it NOMENU.
         #When NOMENU is implemented, also remove the hidden menus.
         make(13003, 
              control.canvas.zoom_reset,
              update_function=control.on_update_image_available_menu_item),
         make(13004, 
              control.canvas.zoom_fit_width,
              update_function=control.on_update_image_available_menu_item),
         make(13005, 
              control.canvas.zoom_fit_height,
              update_function=control.on_update_image_available_menu_item),
         #TODO: All the messaging around this feature is awful but I don't know how to better word it.
         make(13040, 
              control.toggle_spread,
              update_function=control.on_update_spread_toggle_menu_item),
         make(13008, 
              partial(control.canvas.rotate_image, 1),
              update_function=control.on_update_image_available_menu_item),
         make(13009, 
              partial(control.canvas.rotate_image, 0),
              update_function=control.on_update_image_available_menu_item),
         None,
         make(13006, 
              control.toggle_fullscreen,
              update_function=control.on_update_fullscreen_menu_item),
         make(13007, 
              control.toggle_file_list,
              update_function=control.on_update_file_list_menu_item),
         make(13011, 
              control.toggle_thumbnails,
              update_function=control.on_update_thumbnail_menu_item),
         make(13010, 
              control.file_list.toggle_show_hidden,
              update_function=control.file_list.on_update_hidden_menu_item)
        )
        favorites_menu = (
         make(14001, 
              control.add_favorite),
         make(14003, 
              control.add_placeholder),
         make(14002, 
              control.remove_favorite),
         make(14004, 
              control.remove_placeholder),
        )
        favorites_hidden_menu = (
         make(14005, 
              control.open_latest_placeholder),
        )
        help_menu = (
          make(15001, 
               control.open_help),
          make(15002, 
               control.open_feedback),
          make(wx.ID_ABOUT, 
               control.open_about_dialog)
        )
        hidden_menu = (
          make(16001, 
               partial(control.canvas.move_image, MovementType.MOVE_UP, MovementType.MOVETYPE_SMALL)),
          make(16002, 
               partial(control.canvas.move_image, MovementType.MOVE_DOWN, MovementType.MOVETYPE_SMALL)),
          make(16003, 
               partial(control.canvas.move_image, MovementType.MOVE_LEFT, MovementType.MOVETYPE_SMALL)),
          make(16004, 
               partial(control.canvas.move_image, MovementType.MOVE_RIGHT, MovementType.MOVETYPE_SMALL)),
          make(16005, 
               partial(control.canvas.move_image, MovementType.MOVE_UP, MovementType.MOVETYPE_LARGE)),
          make(16006, 
               partial(control.canvas.move_image, MovementType.MOVE_DOWN, MovementType.MOVETYPE_LARGE)),
          make(16007, 
               partial(control.canvas.move_image, MovementType.MOVE_LEFT, MovementType.MOVETYPE_LARGE)),
          make(16008, 
               partial(control.canvas.move_image, MovementType.MOVE_RIGHT, MovementType.MOVETYPE_LARGE)),
          make(16009, 
               partial(control.canvas.move_image, MovementType.MOVE_UP, MovementType.MOVETYPE_FULL)),
          make(16010, 
               partial(control.canvas.move_image, MovementType.MOVE_DOWN, MovementType.MOVETYPE_FULL)),
          make(16011, 
               partial(control.canvas.move_image, MovementType.MOVE_LEFT, MovementType.MOVETYPE_FULL)),
          make(16012, 
               partial(control.canvas.move_image, MovementType.MOVE_RIGHT, MovementType.MOVETYPE_FULL)),
          make(16100, 
               control.canvas.image_drag_end, down_function=control.canvas.image_drag_start),
        )
        fit_menu = (
          make(17001, 
               partial(control.canvas.set_zoom_by_fit_type, Settings.FIT_NONE, save=True)),
          make(17002, 
               partial(control.canvas.set_zoom_by_fit_type, Settings.FIT_WIDTH, save=True)),
          make(17003, 
               partial(control.canvas.set_zoom_by_fit_type, Settings.FIT_HEIGHT, save=True)),
          make(17004, 
               partial(control.canvas.set_zoom_by_fit_type, Settings.FIT_BOTH, save=True)),
          make(17005, 
               partial(control.canvas.set_zoom_by_fit_type, Settings.FIT_WIDTH_OVERSIZE, save=True)),
          make(17006, 
               partial(control.canvas.set_zoom_by_fit_type, Settings.FIT_HEIGHT_OVERSIZE, save=True)),
          make(17007, 
               partial(control.canvas.set_zoom_by_fit_type, Settings.FIT_BOTH_OVERSIZE, save=True)),
          #TODO: (2,2) Add: ask for the custom width?
          make(17008, 
               partial(control.canvas.set_zoom_by_fit_type, Settings.FIT_CUSTOM_WIDTH, save=True)),
        )
        main_menu = (
         make_category(0, 'file', _('&File'), file_menu),
         make_category(1, 'fold', _('F&older'), folder_menu),
         make_category(2, 'view', _('&View'), view_menu),
         make_category(3, 'fav' , _('F&avorites'), favorites_menu),
         make_category(4, 'help', _('&Help'), help_menu),
         make_category(6, '_fit', _('Fit'), fit_menu, True),
        )
        #The fit menu doesn't appear in the top, but can open via right click, so it needs to be created.
        #The other menus here exist to provide commands in the options, but aren't otherwise menus
        #Names can overlap with actual menu names (this is deliberate)
        #Order (first parameter) controls where it will appear in the Settings dialog only
        command_cats = main_menu + (
            make_category(3.1, '_fav', _('Favorites'), favorites_hidden_menu, True),
            make_category(5, '_mov', _('Move'), hidden_menu, True),
        )
        if __debug__:
            #Debug options. Disable when built as an application.
            #Nothing here will be translated, and won't be available as shortcuts.
            debug_menu = (
                make(29900,
                     control.debugController.open_debug_cache_dialog),
                #Maybe an option to change the log level?
                #I can't find any kind of built-in wxpython diagnostics that would be trivial to include.
            )
            main_menu = main_menu + (
                make_category(7, 'debug', 'Debug', debug_menu),
            )
        
        return main_menu, command_cats, commands
    
    @staticmethod
    def _get_toolbar_commands(commands):
        cmd_dict = dict((cmd.ide, cmd) for cmd in commands)
        #TODO: (2,2) Refactor: use constants
        cmd_ids = (12008, 14001, 14002, 12004, 13011)
        return tuple(cmd_dict[id] for id in cmd_ids)
    
    @staticmethod
    def _load_shortcuts(settings, commands):
        if settings.has_section(SHORTCUTS_KEY):
            cmd_dic = dict((cmd.ide, cmd) for cmd in commands)
            items = settings.items(SHORTCUTS_KEY)
            for cmd_id_str, shcut_lst_str in items:
                cmd_id = int(cmd_id_str)
                for shcut_str in shcut_lst_str.split():
                    shcut_lst = shcut_str.split(',')
                    key_code = int(shcut_lst[0])
                    flags = int(shcut_lst[1])
                    shcut = Shortcut(flags, key_code)
                    #TODO *(4,1): catch KeyErrors
                    if cmd_id in cmd_dic:
                        cmd_dic[cmd_id].shortcuts.append(shcut)
        else:
            MenuController._load_default_shortcuts(commands)
            
    @staticmethod
    def _save_shortcuts(settings, commands):
        settings.remove_section(SHORTCUTS_KEY)
        settings.add_section(SHORTCUTS_KEY)
        for cmd in commands:
            cmd_id_str = str(cmd.ide)
            shcut_lst_str = ' '.join(f'{shcut.key_code},{shcut.flags}'
                                     for shcut in cmd.shortcuts)
            settings.set(SHORTCUTS_KEY, cmd_id_str, shcut_lst_str)
    
    @staticmethod
    def _load_default_shortcuts(commands):
        for cmd in commands:
            cmd.load_default_shortcut()
    
    @staticmethod
    def _get_accelerator_table(commands):
        lst = [(shcut.flags, shcut.key_code, cmd.ide) for cmd in commands
               for shcut in cmd.shortcuts]
        return wx.AcceleratorTable(lst)
