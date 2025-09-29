#TODO: (2,3) Refactor: this module and classes were poorly named.
#    this is actually about commands, and not the menu.
import wx
from pubsub import pub as Publisher

from quivilib.i18n import _
from quivilib.model.command import CommandName, Command, SubCommand, CommandCategory, CommandDefinitionList
from quivilib.model.shortcut import Shortcut
from quivilib.control import canvas
from quivilib.model.settings import Settings

SHORTCUTS_KEY = 'Shortcuts'


class MenuController(object):
    def __init__(self, control, settings):
        self.settings = settings
        self.control = control
        self.commands = []
        self.command_definitions = CommandDefinitionList(control)
        
        #TODO: Do more refactoring to split this stuff into separate functions.
        #Additionally, remove the hidden menus from main_menu and track them separately.
        self.main_menu, self.command_cats, self.commands = self._make_commands(self.control)
        self.command_dict = {x.ide: x for x in self.commands}
        self.context_menu = self.create_img_context_menu(self.command_dict)
        self.main_menu = self.main_menu + (self.context_menu,)    #Not ideal but try it for now.
        
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
        self._update_menu_translations()
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

    def _update_menu_translations(self):
        """ Instruct the menu items to update their current translation
        The saved key is re-applied to the translation function.
        """
        #Update menu items
        for cmd in self.commands:
            cmd.update_translation()
        #Update menu categories
        for category in self.main_menu:
            category.update_translation()
    def _make_commands(self, control):
        """Make all commands.
        
        @param control: reference to the main controller instance
        """
        commands = []
        
        def make(ide, **kwparams):
            definition = self.command_definitions.commands[ide]
            command = Command(definition, **kwparams)
            commands.append(command)
            return command
        
        file_menu = (
            make(CommandName.SET_WALLPAPER),
            make(CommandName.COPY),
            make(CommandName.COPY_PATH),
            make(CommandName.DELETE),
            make(CommandName.MOVE),
            None,
            make(CommandName.OPTIONS),
            None,
            make(CommandName.QUIT)
        )
        folder_menu = (
            make(CommandName.SELECT_NEXT),
            make(CommandName.SELECT_PREVIOUS),
            make(CommandName.OPEN_SELECTED_DIRECTORY),
            make(CommandName.OPEN_PARENT),
            make(CommandName.OPEN_NEXT),
            make(CommandName.OPEN_PREVIOUS),
            make(CommandName.REFRESH),
            make(CommandName.OPEN_DIRECTORY, )
        )
        view_menu = (
            make(CommandName.ZOOM_IN),
            make(CommandName.ZOOM_OUT),
            #TODO: Add mouse-specific version that zooms in on mouse position. Also give it NOMENU.
            #When NOMENU is implemented, also remove the hidden menus.
            make(CommandName.ZOOM_FULL),
            make(CommandName.FIT_WIDTH),
            make(CommandName.FIT_HEIGHT),
            #TODO: All the messaging around this feature is awful but I don't know how to better word it.
            make(CommandName.SHOW_SPREAD),
            make(CommandName.ROTATE_CLOCKWISE),
            make(CommandName.ROTATE_COUNTER_CLOCKWISE),
            None,
            make(CommandName.FULL_SCREEN),
            make(CommandName.SHOW_FILE_LIST),
            make(CommandName.SHOW_THUMBNAILS),
            make(CommandName.SHOW_HIDDEN_FILES)
        )
        favorites_menu = (
            make(CommandName.ADD_FAVORITES),
            make(CommandName.ADD_PLACEHOLDER),
            make(CommandName.REMOVE_FAVORITES),
            make(CommandName.REMOVE_PLACEHOLDER),
        )
        favorites_hidden_menu = (
            make(CommandName.OPEN_LAST_PLACEHOLDER),
            make(CommandName.OPEN_CONTEXT_MENU),
        )
        help_menu = (
            make(CommandName.HELP),
            make(CommandName.FEEDBACK),
            make(CommandName.ABOUT, )
        )
        hidden_menu = (
            make(CommandName.MOVE_SMALL_UP),
            make(CommandName.MOVE_SMALL_DOWN),
            make(CommandName.MOVE_SMALL_LEFT),
            make(CommandName.MOVE_SMALL_RIGHT),
            make(CommandName.MOVE_LARGE_UP),
            make(CommandName.MOVE_LARGE_DOWN),
            make(CommandName.MOVE_LARGE_LEFT),
            make(CommandName.MOVE_LARGE_RIGHT),
            make(CommandName.MOVE_FULL_UP),
            make(CommandName.MOVE_FULL_DOWN),
            make(CommandName.MOVE_FULL_LEFT),
            make(CommandName.MOVE_FULL_RIGHT),
            make(CommandName.DRAG_IMAGE)
        )
        fit_menu = (
            make(CommandName.ZOOM_NONE),
            make(CommandName.ZOOM_WIDTH),
            make(CommandName.ZOOM_HEIGHT),
            make(CommandName.ZOOM_WINDOW),
            make(CommandName.ZOOM_WIDTH_LARGER),
            make(CommandName.ZOOM_HEIGHT_LARGER),
            make(CommandName.ZOOM_WINDOW_LARGER),
            #TODO: (2,2) Add: ask for the custom width?
            make(CommandName.ZOOM_CUSTOM_WIDTH),
        )
        main_menu = (
            CommandCategory(0, 'file', '&File', file_menu),
            CommandCategory(1, 'fold', 'F&older', folder_menu),
            CommandCategory(2, 'view', '&View', view_menu),
            CommandCategory(3, 'fav' , 'F&avorites', favorites_menu),
            CommandCategory(4, 'help', '&Help', help_menu),
            CommandCategory(6, '_fit', 'Fit', fit_menu, True),
        )
        #The fit menu doesn't appear in the top, but can open via right click, so it needs to be created.
        #The other menus here exist to provide commands in the options, but aren't otherwise menus
        #Names can overlap with actual menu names (this is deliberate)
        #Order (first parameter) controls where it will appear in the Settings dialog only
        command_cats = main_menu + (
            CommandCategory(3.1, '_fav', 'Favorites', favorites_hidden_menu, True),
            CommandCategory(5, '_mov', 'Move', hidden_menu, True),
        )
        if __debug__:
            #Debug options. Disable when built as an application.
            debug_menu = (
                make(CommandName.CACHE_INFO),
                #Maybe an option to change the log level?
                #I can't find any kind of built-in wxpython diagnostics that would be trivial to include.
            )
            main_menu = main_menu + (
                CommandCategory(7, 'debug', 'Debug', debug_menu),
            )
        
        return main_menu, command_cats, commands
    
    def create_img_context_menu(self, commands: dict[int, Command]):
        """ Create a new context menu that can be opened by a binding command (e.g. right or middle click)
        Unlike other menus, this entirely uses pre-existing commands.
        """
        def make(ide):
            if ide is None:
                return None
            if type(ide) is tuple:
                name, command_list = ide
                lst = [make(x) for x in command_list]
                return SubCommand(name, lst)
            return commands[ide]
        zoomsub_def = ('Zoom', (
            CommandName.ZOOM_IN,   
            CommandName.ZOOM_OUT,  
            CommandName.ZOOM_FULL, 
            CommandName.FIT_WIDTH,
            CommandName.FIT_HEIGHT,
        ))
        rotatesub_def = ('Rotate', (
            CommandName.ROTATE_CLOCKWISE,        
            CommandName.ROTATE_COUNTER_CLOCKWISE,
        ))
        menuitems_def = (
            CommandName.OPEN_DIRECTORY,
            CommandName.SELECT_NEXT,
            CommandName.SELECT_PREVIOUS,
            CommandName.MOVE,
            None,
            zoomsub_def,
            rotatesub_def,
            CommandName.SHOW_SPREAD,
            None,
            CommandName.FULL_SCREEN,
            CommandName.SHOW_FILE_LIST,
            None,
            #favorites,
            #None,
            CommandName.OPTIONS,
            CommandName.HELP,
            CommandName.ABOUT,
            None,
            CommandName.QUIT,
        )
        menuitems = [make(id) for id in menuitems_def]
        return CommandCategory(8, '_ctx', 'Context', menuitems, True)
    
    @staticmethod
    def _get_toolbar_commands(commands):
        cmd_dict = dict((cmd.ide, cmd) for cmd in commands)
        cmd_ids = (
            CommandName.OPEN_DIRECTORY,
            CommandName.ADD_FAVORITES,
            CommandName.REMOVE_FAVORITES,
            CommandName.OPEN_PARENT,
            CommandName.SHOW_THUMBNAILS
        )
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
