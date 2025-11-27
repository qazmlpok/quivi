from quivilib.i18n import _
from quivilib.model.shortcut import Shortcut
from quivilib.model.commandlist import CommandDefinition, MenuDefinition
from quivilib.model.commandenum import CommandName, CommandFlags

from typing import Protocol


class QuiviMenuItem(Protocol):
    """ Something that can appear within a menu. Either a single menu item (with executable command(s)),
    or a list of other QuiviMenuItems that will appear as a submenu.
    """
    def update_translation(self):
        pass
    name: str
    ide: int    #CommandName|MenuName

class Command(QuiviMenuItem):
    def __init__(self, definition: CommandDefinition):
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
        self.category = self.categoryKey = definition.categoryKey
        self.default_shortcuts = definition.shortcuts
        self.shortcuts: list[Shortcut] = []
        self.flags = definition.flags
        self.update_translation()
        
        self._function = definition.function
        self.update_function = definition.update_function
        self._down_function = definition.down_function
        
    def update_translation(self):
        #dumb hack to avoid translating the debug menu option stuff.
        if self.ide < CommandName.CACHE_INFO:
            self.name = _(self.nameKey)
            self.description = _(self.descrKey)
            self.category = _(self.categoryKey)

    def load_default_shortcut(self):
        if self.default_shortcuts:
            self.shortcuts = self.default_shortcuts
        
    def __call__(self):
        self._function()
        
    def on_down(self):
        if self._down_function is not None:
            self._down_function()
        
    def __repr__(self):
        return f"{self.ide}: '{self.clean_name}' - {self.description}"
    
    @staticmethod
    def clean_str(s):
        return s.replace('&', '').replace('...', '')
    
    @property
    def name_and_shortcut(self):
        if self.shortcuts:
            return f'{self.name}\t{self.shortcuts[0].name}'
        else:
            return self.name
    
    @property
    def name_and_category(self):
        return f'{self.clean_str(self.category)} | {self.clean_str(self.name)}'
    
    @property
    def clean_name(self):
        return self.clean_str(self.name)
    
    @property
    def checkable(self) -> bool:
        return (self.flags & CommandFlags.CHECKABLE) != 0
#

class CommandCategory(QuiviMenuItem):
    def __init__(self, definition: MenuDefinition):
        """ Create a new command category from the provided definition
        """
        self.idx = definition.menu_id
        self.commands = definition.commands
        self.name = self.nameKey = definition.nameKey
        
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
