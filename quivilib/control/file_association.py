from quivilib import util

from quivilib.i18n import _
from quivilib.model.image import get_supported_extensions
from quivilib.thirdparty.path import path as Path

from ConfigParser import SafeConfigParser, NoOptionError, NoSectionError
import logging
log = logging
try:
    import _winreg as reg
except ImportError:
    reg = None


SKIP_EXT = ('.psd', '.ico')

(CURRENT_USER,
 ALL_USERS) = range(2)
 
ICON_ID = 2

PROG_ID_NAME = 'Quivi'
CONFIG_INI = 'config.ini'

SOFTWARE_CLASSES = 'Software\\Classes\\'



def parse_command_line(argv, main_script):
    if len(argv) > 1 and argv[1] == '/register':
        fam = AssociationManager(Path(main_script))
        user = None
        if len(argv) > 2:
            if argv[2] == 'all':
                user = ALL_USERS
            elif argv[2] == 'current':
                user = CURRENT_USER
        if not user:
            user = fam.get_user()
        fam.register_defaults(user)
        return True
    elif len(argv) > 1 and argv[1] == '/unregister':
        fam = AssociationManager(Path(main_script))
        user = fam.get_user()
        fam.unregister_all(user)
        return True
    return False
            
def get_root_key(user):
    if user == CURRENT_USER:
        return reg.HKEY_CURRENT_USER
    else:
        return reg.HKEY_LOCAL_MACHINE
    
def recursive_delete_key(key, sub_key):
    key_to_delete = reg.OpenKey(key, sub_key, 0, reg.KEY_ALL_ACCESS)
    try:
        while True:
            child_name = reg.EnumKey(key_to_delete, 0)
            recursive_delete_key(key_to_delete, child_name)
    except EnvironmentError, e:
        pass
    reg.CloseKey(key_to_delete)
    reg.DeleteKey(key, sub_key)

def get_prog_id_name(ext):
        return PROG_ID_NAME + ext    


    
class Action(object):
    def __init__(self, name, command):
        self.name = name
        self.command = command
 
 
 
class ProgId(object):
    def __init__(self, name, friendly_name, user):
        self.name = name
        self.friendly_name = friendly_name
        self.user = user
        self.root_key = get_root_key(self.user)
        self.key_name = SOFTWARE_CLASSES + name
        self.default_icon = ''
        
    @staticmethod
    def load(name, user):
        key = reg.OpenKey(get_root_key(user), SOFTWARE_CLASSES + name)
        friendly_name = reg.QueryValueEx(key, '')[0]
        prog_id = ProgId(name, friendly_name, user)
        default_icon_key = reg.CreateKey(key, 'DefaultIcon')
        prog_id.default_icon = reg.QueryValueEx(default_icon_key, '')[0]
        return prog_id
    
    @staticmethod
    def exists(name, user):
        try:
            key = reg.OpenKey(get_root_key(user), SOFTWARE_CLASSES + name)
            return True
        except EnvironmentError:
            return False
        
    @staticmethod
    def remove(name, user):
        recursive_delete_key(get_root_key(user), SOFTWARE_CLASSES + name)
    
    def save(self):
        key = reg.CreateKey(self.root_key, self.key_name)
        reg.SetValueEx(key, '', 0, reg.REG_SZ, self.friendly_name)
        default_icon_key = reg.CreateKey(key, 'DefaultIcon')
        reg.SetValueEx(default_icon_key, '', 0, reg.REG_SZ, self.default_icon)
        
    def add_action(self, action):
        key = reg.CreateKey(self.root_key, self.key_name + r'\shell\%s\command' % action.name)
        reg.SetValueEx(key, '', 0, reg.REG_SZ, action.command)

    def get_action(self, action_name):
        key = reg.OpenKey(self.root_key, self.key_name + r'\shell\%s\command' % action_name, 0, reg.KEY_READ)
        command = reg.QueryValueEx(key, '')[0]
        return Action(action_name, command)



class FileType(object):
    def __init__(self, ext, prog_id_name, user):
        self.ext = ext
        self.prog_id_name = prog_id_name
        self.user = user
        self.perceived_type = None
        self.content_type = None
        self.root_key = get_root_key(self.user)
        
    @staticmethod
    def load(ext, user):
        ft = FileType(ext, '', user)
        key = reg.OpenKey(get_root_key(user), SOFTWARE_CLASSES + ext, 0, reg.KEY_READ)
        try:
            ft.content_type = reg.QueryValueEx(key, 'Content Type')[0]
        except EnvironmentError:
            pass
        try:
            ft.perceived_type = reg.QueryValueEx(key, 'PerceivedType')[0]
        except EnvironmentError:
            pass
        ft.prog_id_name = reg.QueryValueEx(key, '')[0]
        return ft
    
    @staticmethod
    def exists(ext, user):
        try:
            reg.OpenKey(get_root_key(user), SOFTWARE_CLASSES + ext, 0, reg.KEY_READ)
            return True
        except EnvironmentError:
            return False
        
    @staticmethod
    def remove(ext, user):
        recursive_delete_key(get_root_key(user), SOFTWARE_CLASSES + ext)
        
    def save(self, backup=False):
        key = reg.CreateKey(self.root_key, SOFTWARE_CLASSES + self.ext)
        if backup:
            try:
                old_prog_id = reg.QueryValueEx(key, '')[0]
            except EnvironmentError:
                old_prog_id = None
            if old_prog_id and old_prog_id != self.prog_id_name:
                reg.SetValueEx(key, '_backup_', 0, reg.REG_SZ, old_prog_id)
        reg.SetValueEx(key, '', 0, reg.REG_SZ, self.prog_id_name)
        if self.perceived_type:
            reg.SetValueEx(key, 'PerceivedType', 0, reg.REG_SZ, self.perceived_type)
        if self.content_type:
            reg.SetValueEx(key, 'Content Type', 0, reg.REG_SZ, self.content_type)
        
    def restore_backup(self, original_prog_id_name):
        key = reg.CreateKey(self.root_key, SOFTWARE_CLASSES + self.ext)
        restored = False
        actual_prog_id = reg.QueryValueEx(key, '')[0]
        if original_prog_id_name == '' or actual_prog_id == original_prog_id_name:
            try:
                backup = reg.QueryValueEx(key, '_backup_')[0]
            except EnvironmentError:
                backup = None
            if backup:
                reg.SetValueEx(key, '', 0, reg.REG_SZ, backup)
                restored = True
        try:
            reg.DeleteValue(key, '_backup_')
        except EnvironmentError:
            pass
        return restored
                
    def add_prog_id(self, prog_id):
        key = reg.CreateKey(self.root_key, SOFTWARE_CLASSES + self.ext + r'\OpenWithProgids')
        reg.SetValueEx(key, prog_id, 0, reg.REG_NONE, '')
        
    def remove_prog_id(self, prog_id):
        key = reg.CreateKey(self.root_key, SOFTWARE_CLASSES + self.ext + r'\OpenWithProgids')
        reg.DeleteValue(key, prog_id)
        


class AssociationManager(object):
    
    def __init__(self, main_script_path):
        self.main_script_path = main_script_path

    def register_defaults(self, user):
        for ext in get_supported_extensions():
            if ext in SKIP_EXT:
                continue
            desc = self._get_ext_description(ext)
            prog_id = self.register_prog_id(user, ext, desc, self.get_open_command())
            self.register_extension(user, ext, prog_id.name)
            
    def unregister_all(self, user):
        for ext in get_supported_extensions():
            if ext in SKIP_EXT:
                continue
            prog_id_name = get_prog_id_name(ext)
            try:
                command = ProgId.load(prog_id_name, user).get_action('open').command
                if command == self.get_open_command():
                    ProgId.remove(prog_id_name, user)
                else:
                    #ProgId taken by another program
                    continue
            except EnvironmentError:
                pass
            
            ft = FileType.load(ext, user)
            ft.remove_prog_id(prog_id_name)
            #check if extension is taken by us
            if ft.prog_id_name == prog_id_name:
                ft.restore_backup(prog_id_name)
                ft = FileType.load(ext, user)
                if ft.prog_id_name == prog_id_name:
                    FileType.remove(ext, user)
                    
    def register_prog_id(self, user, ext, friendly_name, command):
        prog_id = ProgId(get_prog_id_name(ext), friendly_name, user)
        prog_id.default_icon = util.get_exe_path() + ',-' + str(ICON_ID)
        prog_id.save()
        prog_id.add_action(Action('open', command))
        return prog_id
    
    def register_extension(self, user, ext, prog_id_name):
        exists = False
        file_type = FileType(ext, prog_id_name, user)
        file_type.perceived_type = 'image'
        
        if user == CURRENT_USER and FileType.exists(ext, CURRENT_USER):
            try:
                file_type = FileType.load(ext, user)
                exists = True
            except EnvironmentError:
                pass
        elif FileType.exists(ext, ALL_USERS):
            try:
                if file_type.user != user:
                    file_type.user = user
                exists = True
            except EnvironmentError:
                pass
        
        file_type.prog_id_name = prog_id_name
        will_register = (ext not in SKIP_EXT)
        if not exists or will_register:
            file_type.save(True)
        file_type.add_prog_id(prog_id_name)
    
    def get_open_command(self):
        if util.is_frozen():
            return '"%s" "%%1"' % util.get_exe_path()
        else:
            return '"%s" "%s" "%%1"' % (util.get_exe_path(), self.main_script_path)
    
    def get_user(self):
        if util.is_frozen():
            ini_path = util.get_exe_path().dirname() / CONFIG_INI
        else:
            ini_path = self.main_script_path.dirname() / CONFIG_INI
        ini = SafeConfigParser()
        try:
            ini.read(ini_path)
            if ini.get('config', 'user') == 'current':
                return CURRENT_USER
        except (NoOptionError, NoSectionError):
            pass
        return ALL_USERS

    @staticmethod
    def _get_ext_description(ext):
        return '%s %s' % (ext[1:].upper(), _('Image'))
    