from enum import IntEnum, Flag
import wx

from quivilib.i18n import _
from quivilib.model.shortcut import Shortcut
from quivilib.model.commandlist import *

class Command():
    def __init__(self, definition: CommandDefinition, function, 
            down_function=None, update_function=None):
        """
            Create a new command category.
            
            @param ide: Unique identifier for this command
            @param name: Display name for this command. Translated, will include &.
            @param description: Description for this command. Translated.
            @param function: Function to execute upon selecting this command.
            @param default_shortcuts: Default keyboard combination for this command
            @param flags: Flags for controlling where this command can be used, i.e. keyboard/mouse
            @param down_function: For mouse events, command to execute on mouse down
            @param checkable: If true, potentially show a checkmark in the menu (ref update_function)
            @param update_function: Function used to modify display of this menu item, e.g. to disable it or to check the checkbox.
        """
        self.ide = definition.uid
        self.name = self.nameKey = definition.nameKey
        self.description = self.descrKey = definition.descrKey
        self._function = function
        self._down_function = down_function
        self.default_shortcuts = definition.shortcuts
        self.shortcuts = []
        self.checkable = (definition.flags&CommandFlags.CHECKABLE)
        self.update_function = update_function
        self.flags = definition.flags
        if self.flags is None:
            self.flags = Command.KBM
        self.update_translation(definition)
        
        need_update = (definition.flags & CommandFlags.NEED_UPDATE) != 0
        #Some consistency checks
        if (need_update and update_function is None):
            print(definition.flags)
            raise Exception(f"Menu item {self.clean_name} requires an update function but doesn't have one")
        if (not need_update and update_function is not None):
            raise Exception(f"Menu item {self.clean_name} was given an update function but can't use one")
        
    def update_translation(self, definition):
        #dumb hack to avoid translating the debug menu option stuff.
        if self.ide < CommandName.CACHE_INFO:
            self.name = _(self.nameKey)
            self.description = _(self.descrKey)

    def load_default_shortcut(self):
        if self.default_shortcuts:
            self.shortcuts = self.default_shortcuts
        
    def __call__(self):
        self._function()
        
    def on_down(self):
        if self._down_function is not None:
            self._down_function()
        
    def __repr__(self):
        return f'{self.clean_name}: {self.description}'
        
    @property
    def name_and_shortcut(self):
        if self.shortcuts:
            return f'{self.name}\t{self.shortcuts[0].name}'
        else:
            return self.name
    
    @property
    def clean_name(self):
        return self.name.replace('&', '').replace('...', '')
#

class CommandCategory():
    def __init__(self, order: int, idx: str, name: str, commands: list[Command], hidden=False):
        """
            Create a new command category.
            
            @param order: The order within the Options menu (not used elsewhere)
            @param idx: string key to use as a unique identifier for this menu. Needed for updates.
            @param commands: Collection of commands (e.g. menu items) associated with this category.
            @param name: Display name for the menu - translated to the target language
            @param hidden: If true, the menu will be created but not added to the menu bar.
        """
        self.order = order
        self.idx = idx
        self.commands = commands
        self.name = name
        self.hidden = hidden
        
        #From what I'm seeing, the only way to find a menu is by the position or by the title.
        #Title poses problems when trying to update translations.
        #So to work around this, store the id when inserting the menu into the bar.
        #This will be set when the menu is built.
        self.menu_idx = -1
        
    @property
    def clean_name(self):
        return self.name.replace('&', '')
#
