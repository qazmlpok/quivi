

#TODO (2,4): Improve: these tests suck; it shouldn't actually touch
#    the registry and should use mock objects.

import unittest
import sys
if sys.platform == 'win32':
    import winreg as R
else:
    R = None

from quivilib.control import file_association as F


class Test(unittest.TestCase):
        
    def test_load_prog_id(self):
        if not R:
            return
        pid = F.ProgId.load('Python.File', F.ALL_USERS)
        self.assertEqual(pid.friendly_name, 'Python File')
        self.assertEqual(pid.default_icon, r'C:\Python26\DLLs\py.ico')
        
    def test_save_prog_id(self):
        if not R:
            return
        self.assertFalse(F.ProgId.exists('QuiviTest.Test', F.CURRENT_USER))
        
        pid = F.ProgId('QuiviTest.Test', 'Quivi Test', F.CURRENT_USER)
        action = F.Action('open', '"quivi.exe" "%1"')
        pid.add_action(action)
        pid.save()
        npid = F.ProgId.load('QuiviTest.Test', F.CURRENT_USER)
        naction = pid.get_action(action.name)
        
        self.assertEqual(pid.name, npid.name)
        self.assertEqual(pid.friendly_name, npid.friendly_name)
        self.assertEqual(pid.user, npid.user)
        
        self.assertEqual(action.name, naction.name)
        self.assertEqual(action.command, naction.command)
        
        self.assertTrue(F.ProgId.exists('QuiviTest.Test', F.CURRENT_USER))
        
        F.ProgId.remove('QuiviTest.Test', F.CURRENT_USER)
        
        self.assertFalse(F.ProgId.exists('QuiviTest.Test', F.CURRENT_USER))
        
        def test_load():
            F.ProgId.load('QuiviTest.Test', F.CURRENT_USER)
            
        self.assertRaises(EnvironmentError, test_load)
        
    def test_load_file_type(self):
        if not R:
            return
        ft = F.FileType.load('.py', F.ALL_USERS)
        self.assertEqual(ft.prog_id_name, 'Python.File')
        self.assertEqual(ft.content_type, 'text/plain')
        
    def test_save_file_type(self):
        if not R:
            return
        try:
            F.FileType.remove('.quivi_test', F.CURRENT_USER)
        except:
            pass
        
        ft = F.FileType('.quivi_test', 'Quivi.Test', F.CURRENT_USER)
        ft.save(False)
        ft.save(True)
        nft = F.FileType.load('.quivi_test', F.CURRENT_USER)
        
        self.assertEqual(ft.ext, nft.ext)
        self.assertEqual(ft.prog_id_name, nft.prog_id_name)
        
        ft.content_type = 'text/plain'
        ft.save(False)
        nft = F.FileType.load('.quivi_test', F.CURRENT_USER)
        
        self.assertEqual(ft.ext, nft.ext)
        self.assertEqual(ft.prog_id_name, nft.prog_id_name)
        self.assertEqual(ft.content_type, nft.content_type)
        
        ft.perceived_type = 'text'
        ft.save(False)
        nft = F.FileType.load('.quivi_test', F.CURRENT_USER)
        
        self.assertEqual(ft.ext, nft.ext)
        self.assertEqual(ft.prog_id_name, nft.prog_id_name)
        self.assertEqual(ft.content_type, nft.content_type)
        self.assertEqual(ft.perceived_type, nft.perceived_type)
        
        self.assertTrue(F.FileType.exists('.quivi_test', F.CURRENT_USER))
        
        F.FileType.remove('.quivi_test', F.CURRENT_USER)
        
        self.assertFalse(F.FileType.exists('.quivi_test', F.CURRENT_USER))
        
        def test_load():
            F.FileType.load('.quivi_test', F.CURRENT_USER)
            
        self.assertRaises(EnvironmentError, test_load)
        
    def test_file_type_save_with_backup(self):
        if not R:
            return
        try:
            F.FileType.remove('.quivi_test', F.CURRENT_USER)
        except:
            pass
        ft = F.FileType('.quivi_test', 'Quivi2.Test', F.CURRENT_USER)
        ft.save(False)
        ft = F.FileType('.quivi_test', 'Quivi.Test', F.CURRENT_USER)
        ft.save(True)
        key = R.OpenKey(R.HKEY_CURRENT_USER, F.SOFTWARE_CLASSES + r'.quivi_test')
        prog_id = R.QueryValueEx(key, '')[0]
        
        self.assertEqual(prog_id, 'Quivi.Test')
        
        backup_id = R.QueryValueEx(key, '_backup_')[0]
        
        self.assertEqual(backup_id, 'Quivi2.Test')
        
        ft.restore_backup('Quivi.Test')
        prog_id = R.QueryValueEx(key, '')[0]
        
        self.assertEqual(prog_id, 'Quivi2.Test')
        
        F.FileType.remove('.quivi_test', F.CURRENT_USER)
    
    def test_save_with_backup_no_previous(self):
        if not R:
            return
        try:
            F.FileType.remove('.quivi_test', F.CURRENT_USER)
        except:
            pass
        
        ft = F.FileType('.quivi_test', 'Quivi.Test', F.CURRENT_USER)
        ft.save(True)
        key = R.OpenKey(R.HKEY_CURRENT_USER, F.SOFTWARE_CLASSES + r'.quivi_test')
        fn = lambda: R.QueryValueEx(key, '_backup_')
        self.assertRaises(EnvironmentError, fn)
        
        ft.restore_backup('Quivi.Test')
        
        F.FileType.remove('.quivi_test', F.CURRENT_USER)
        
    def test_add_prog_id(self):
        if not R:
            return
        try:
            F.FileType.remove('.quivi_test', F.CURRENT_USER)
        except:
            pass
        
        ft = F.FileType('.quivi_test', 'Quivi.Test', F.CURRENT_USER)
        ft.save()
        ft.add_prog_id('Quivi2.Test')
        ft.remove_prog_id('Quivi2.Test')
        
        F.FileType.remove('.quivi_test', F.CURRENT_USER)
        
    def test_get_prog_id_name(self):
        if not R:
            return
        self.assertEqual(F.get_prog_id_name('.quivi'), 'Quivi.quivi')
        
    def test_get_open_command(self):
        if not R:
            return
        py_path = sys.executable
        path = r'C:\Program Files\Quivi\Quivi.exe'
        am = F.AssociationManager(path)
        self.assertEqual(am.get_open_command(), f'"{py_path}" "{path}" "%1"')

    def test_recursive_delete_key(self):
        if not R:
            return
        key = R.CreateKey(R.HKEY_CURRENT_USER, '__Temp')
        sub_key = R.CreateKey(key, 'Foo')
        R.CreateKey(key, 'Bar')
        R.CreateKey(sub_key, 'Spam')
        R.CreateKey(sub_key, 'Eggs')
        R.CloseKey(key)
        F.recursive_delete_key(R.HKEY_CURRENT_USER, '__Temp')
        def test():
            R.OpenKey(R.HKEY_CURRENT_USER, '__Temp')
        self.assertRaises(EnvironmentError, test)
        
        