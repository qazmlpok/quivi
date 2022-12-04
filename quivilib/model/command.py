



class CommandCategory(object):
    def __init__(self, order, idx, name, commands, hidden=False):
        """
            Create a new command category.
            
            @param order: The order within the Options menu (not used elsewhere)
            @param idx: String key to use as a unique identifier for this menu. Needed for updates.
            @param commands: Collection of commands (e.g. menu items) associated with this category.
            @param name: Display name for the menu - translated to the target language
            @param hidden: If true, the menu will be created but not added to the menu bar.
        """
        self.order = order
        self.idx = idx
        self.commands = commands
        self.name = name
        self.hidden = hidden
        
    @property
    def clean_name(self):
        return self.name.replace('&', '')
    
    
class Command(object):
    (
        KB,         #Command can be assigned to a keyboard shortcut
        MOUSE,      #Command can be assigned to a mouse button
        NOMENU,     #Command does not appear in the application menu
    ) = (1 << x for x in range(3))
    KBM = KB|MOUSE

    def __init__(self, ide, name, description, function, default_shortcuts, 
            flags=None, down_function=None, checkable=False, update_function=None):
        self.ide = ide
        self.name = name
        self.description = description
        self._function = function
        self._down_function = down_function
        self.default_shortcuts = default_shortcuts
        self.shortcuts = []
        self.checkable = checkable
        self.update_function = update_function
        self.flags = flags
        if self.flags is None:
            self.flags = Command.KBM
        
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
