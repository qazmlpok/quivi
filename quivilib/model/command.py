from enum import IntEnum, Flag
import wx

from quivilib.i18n import _
from quivilib.model.shortcut import Shortcut
from quivilib.model.commandlist import *

from typing import Protocol

class MenuItem(Protocol):
    """ Something that can appear within a menu. Either a single menu item (with executable command(s)),
    or a list of other MenuItems that will appear as a submenu.. 
    """
    def update_translation(self):
        pass
    name: str
    ide: int

class Command(MenuItem):
    def __init__(self, definition: CommandDefinition, function, down_function=None, update_function=None):
        """
            Create a new command category.
            
            @param definition: Static definition for the command; contains most fields.
            @param function: Function to execute upon selecting this command.
            @param down_function: For mouse events, command to execute on mouse down
            @param update_function: Function used to modify display of this menu item, e.g. to disable it or to check the checkbox.
        """
        self.ide = definition.uid
        self.name = self.nameKey = definition.nameKey
        self.description = self.descrKey = definition.descrKey
        self.default_shortcuts = definition.shortcuts
        self.shortcuts: list[Shortcut] = []
        self.flags = definition.flags
        self.update_translation()
        
        self._function = function
        self.update_function = update_function
        self._down_function = down_function
        
        need_update = (definition.flags & CommandFlags.NEED_UPDATE) != 0
        #Some consistency checks
        if (need_update and update_function is None):
            raise Exception(f"Menu item {self.clean_name} requires an update function but doesn't have one")
        if (not need_update and update_function is not None):
            raise Exception(f"Menu item {self.clean_name} was given an update function but can't use one")
        
    def update_translation(self):
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
    
    @property
    def checkable(self) -> bool:
        return (self.flags & CommandFlags.CHECKABLE) != 0
#

class SubCommand(MenuItem):
    """ A submenu that contains other menu items.
    Not to be confused with a CommandCategory, which is a top-level menubar item.
    That has other fields, rightly or wrongly, and shouldn't be nested within another menu.
    """
    def __init__(self, descrKey: str, items: list[MenuItem]):
        self.description = self.descrKey = descrKey
        self.items = items
        self.ide = 0
        
        self.update_translation()
        
    def update_translation(self):
        self.description = _(self.descrKey)
        #This isn't actually necessary because everything should already have been updated.
        #As a result, this should be reworked to be applied to a flat list of everything, not here.
        for i in self.items:
            i.update_translation()

    @property
    def name_and_shortcut(self):
        return self.description

class CommandCategory():
    def __init__(self, order: int, idx: str, nameKey: str, commands: list[MenuItem], hidden=False):
        """
            Create a new command category.
            
            @param order: The order within the Options menu (not used elsewhere)
            @param idx: string key to use as a unique identifier for this menu. Needed for updates.
            @param commands: Collection of commands (e.g. menu items) associated with this category.
            @param nameKey: Display name for the menu - will be translated to the target language
            @param hidden: If true, the menu will be created but not added to the menu bar.
        """
        self.order = order
        self.idx = idx
        self.commands = commands
        self.name = self.nameKey = nameKey
        self.hidden = hidden
        
        #From what I'm seeing, the only way to find a menu is by the position or by the title.
        #Title poses problems when trying to update translations.
        #So to work around this, store the id when inserting the menu into the bar.
        #This will be set when the menu is built.
        self.menu_idx = -1
        
        self.update_translation()

    def update_translation(self):
        #dumb hack to avoid translating the debug menu option stuff.
        if self.nameKey != 'Debug':
            self.name = _(self.nameKey)
        
    @property
    def clean_name(self):
        return self.name.replace('&', '')
#
