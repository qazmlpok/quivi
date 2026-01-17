#TODO: (2,3) Refactor: this module and classes were poorly named.
#    this is actually about commands, and not the menu.
import wx
from pubsub import pub as Publisher

from quivilib.model.command import Command, CommandCategory
from quivilib.model.commandlist import *
from quivilib.model.shortcut import Shortcut

SHORTCUTS_KEY = 'Shortcuts'


class MenuController(object):
    def __init__(self, control, settings):
        self.settings = settings
        self.control = control
        self.command_definitions = CommandDefinitionList(control)
        self.menu_definitions = MenuDefinitionList()

        #Convert the definitions to actual menu items.
        self.commands = [Command(x) for x in self.command_definitions.cmd_list]
        menus = [CommandCategory(x) for x in self.menu_definitions.menu_list]

        #Lookup for all menus - needed for submenus and context menus.
        self.menu_dict = {x.idx: x for x in menus}

        #Items that appear on the main menu. ID only.
        self.main_menu = [x.menu_id for x in self.menu_definitions.menubar_menus]

        self._load_shortcuts(self.settings, self.commands)      #Probably needs a rework.
        self.shortcuts = self._get_accelerator_table(self.commands)
        #These must be sent in this order
        Publisher.sendMessage('menu.built', main_menu=self.main_menu, all_menus=menus, commands=self.commands)
        Publisher.sendMessage('toolbar.built', commands=self._get_toolbar_commands(self.commands))
        #TODO: (2,2) Refactor: change this message name. This also notifies that
        #    shortcuts have changed.
        Publisher.sendMessage('menu.shortcuts.changed', accel_table=self.shortcuts)
        Publisher.sendMessage('menu.labels.changed', categories=menus)
        
        Publisher.subscribe(self.on_language_changed, 'language.changed')
        Publisher.subscribe(self.on_command_execute, 'command.execute')
        Publisher.subscribe(self.on_menu_added, 'menu.item_added')
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
        Publisher.sendMessage('menu.shortcuts.changed', accel_table=self.shortcuts)
        
    def on_language_changed(self):
        self._update_menu_translations()
        menus = list(self.menu_dict.values())
        Publisher.sendMessage('menu.labels.changed', categories=menus)
        Publisher.sendMessage('toolbar.labels.changed', commands=self._get_toolbar_commands(self.commands))
        
    def on_menu_added(self, *, cmd: MenuName, idx: int):
        """ Called when a new item is added to the menu bar (i.e. the downloads menu).
        This class has no access to the actual menubar; the main gui has no access to these definitions
        """
        if cmd in self.menu_dict:
            self.menu_dict[cmd].menu_idx = idx
        elif __debug__:
            raise Error('Unknown menu item ' + cmd)
        
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
        for catid in self.menu_dict:
            self.menu_dict[catid].update_translation()

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
        return tuple(cmd_dict[ide] for ide in cmd_ids)
    
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
