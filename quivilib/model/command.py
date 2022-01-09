



class CommandCategory(object):
    def __init__(self, name, commands):
        self.commands = commands
        self.name = name
        
    @property
    def clean_name(self):
        s = self.name
        s = s.replace('&', '')
        return s
    
    
class Command(object):
    def __init__(self, ide, name, description, function, default_shortcuts, checkable=False, update_function=None):
        self.ide = ide
        self.name = name
        self.description = description
        self._function = function
        self.default_shortcuts = default_shortcuts
        self.shortcuts = []
        self.checkable = checkable
        self.update_function = update_function
        
    def load_default_shortcut(self):
        if self.default_shortcuts:
            self.shortcuts = self.default_shortcuts
        
    def __call__(self):
        self._function()
        
    @property
    def name_and_shortcut(self):
        if self.shortcuts:
            return '%s\t%s' % (self.name, self.shortcuts[0].name)
        else:
            return self.name
    
    @property
    def clean_name(self):
        s = self.name
        s = s.replace('&', '')
        s = s.replace('...', '')
        return s
