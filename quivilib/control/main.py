from __future__ import with_statement, absolute_import

from quivilib import meta
from quivilib.model import App
from quivilib.model.settings import Settings
from quivilib.gui.main import MainWindow
from quivilib.gui.art import QuiviArtProvider 
from quivilib.control.file_list import FileListController
from quivilib.control.menu import MenuController
from quivilib.control.canvas import CanvasController
from quivilib.control.wallpaper import WallpaperController
from quivilib.control.options import OptionsController
from quivilib.control.cache import ImageCache
from quivilib.control.check_update import UpdateChecker
from quivilib.control.i18n import I18NController
from quivilib.thirdparty.path import path as Path
from quivilib import util

import wx
from wx.lib.pubsub import pub as Publisher

import string
import logging as log
import traceback
import sys



class MainController(object):
    #TODO: (1,3) Refactor: move 'favorites.changed' events to the model?
    
    
    INI_FILE_NAME = u'pyquivi.ini'
    LOG_FILE_NAME = u'quivi.log' 
    STDIO_FILE_NAME = u'error.log' 
    
    def __init__(self, main_script, file_to_open):
        self.main_script = Path(main_script)
        wx.GetApp().SetAppName(meta.APPNAME)
        
        try:
            Path(wx.StandardPaths.Get().GetUserDataDir()).mkdir()
        except:
            pass
        
        if meta.DEBUG:
            log.basicConfig()
        else:
            log_file = Path(wx.StandardPaths.Get().GetUserDataDir()) / self.LOG_FILE_NAME
            log.basicConfig(filename=log_file, filemode='w')
        log.getLogger().setLevel(meta.LOG_LEVEL)
        
        wx.ArtProvider.PushProvider(QuiviArtProvider())
        
        if self.can_save_settings_locally():
            settings_path = self.program_path / self.INI_FILE_NAME
            stdio_path = self.program_path / self.STDIO_FILE_NAME
        else:
            settings_path = Path(wx.StandardPaths.Get().GetUserDataDir()) / self.INI_FILE_NAME
            stdio_path = Path(wx.StandardPaths.Get().GetUserDataDir()) / self.STDIO_FILE_NAME
        self.settings = Settings(settings_path)
        start_dir = self._get_start_dir(self.settings)
        self.temp_dir = self._get_temp_dir()
        if util.is_frozen():
            sys.stdout = sys.stderr = stdio_path.open('w')
        
        self.view = MainWindow()
        
        self.model = App(self.settings, start_dir)
        self.model.canvas.set_view(self.view.canvas_view)
        
        self.i18n = I18NController(self, self.settings)
        self.cache = ImageCache(self.settings)
        self.file_list = FileListController(self.model, self.model.container)
        self.canvas = CanvasController('canvas', self.model.canvas,
                                       self.view.canvas_view, self.settings)
        self.wallpaper = WallpaperController(self.model)
        self.options = OptionsController(self, self.model)
        #This must be the last controller created (it references the others)
        self.menu = MenuController(self, self.settings)
        
        Publisher.subscribe(self.on_program_closed, 'program.closed')
        Publisher.subscribe(self.on_open_update_site, 'program.open_update_site')
        Publisher.subscribe(self.on_request_temp_path, 'request.temp_path')
        Publisher.sendMessage('favorites.changed', self.model.favorites)
        Publisher.sendMessage('settings.loaded', self.model.settings)
        
        self.pane_info = None
        
        if file_to_open:
            self.file_list.open_path(file_to_open)
            
        self.update_checker = UpdateChecker(self.settings)
        
    def quit(self):
        self.view.Close()
        
    def toggle_fullscreen(self):
        if self.settings.get('Options', 'RealFullscreen') == '1':
            style = wx.FULLSCREEN_ALL
        else:
            style = (wx.FULLSCREEN_NOBORDER | wx.FULLSCREEN_NOCAPTION)
        self.view.ShowFullScreen(not self.view.IsFullScreen(), style)
        
    def on_update_fullscreen_menu_item(self, event):
        event.Check(self.view.IsFullScreen())
        
    def toggle_file_list(self):
        #TODO: *(2,?) Fix: panel is not always restored with its previous size.
        #      Ask wxPython people?
        pane = self.view.aui_mgr.GetPane('file_list')
        if pane.IsShown():
            pane.BestSize(self.view.file_list_panel.GetSizeTuple())
        show = not pane.IsShown() 
        pane.Show(show)
        self.view.aui_mgr.Update()
        
    def on_update_file_list_menu_item(self, event):
        pane = self.view.aui_mgr.GetPane('file_list')
        event.Check(pane.IsShown())
        
    def toggle_thumbnails(self):
        pane = self.view.file_list_panel
        pane.toggle_thumbnails()
    
    def on_update_thumbnail_menu_item(self, event):
        pane = self.view.file_list_panel
        event.Check(pane.is_thumbnails())
        
    def add_favorite(self):
        path = self.model.container.universal_path
        if path:
            self.model.favorites.insert(path)
            Publisher.sendMessage('favorites.changed', self.model.favorites)
            Publisher.sendMessage('favorite.opened', True)
        
    def remove_favorite(self):
        self.model.favorites.remove(self.model.container.path)
        Publisher.sendMessage('favorites.changed', self.model.favorites)
        Publisher.sendMessage('favorite.opened', False)
        
    def copy_to_clipboard(self):
        self.model.canvas.copy_to_clipboard()
        
    def delete(self):
        self.file_list.delete(self.view)
        
    def open_about_dialog(self):
        Publisher.sendMessage('about.open_dialog', None)
        
    def open_help(self):
        import webbrowser
        webbrowser.open(meta.HELP_URL)
        
    def open_feedback(self):
        import webbrowser
        webbrowser.open(meta.REPORT_URL)
        
    def on_open_update_site(self, message):
        import webbrowser
        webbrowser.open(message.data)
        
    def on_program_closed(self, message):
        settings_lst = message.data
        for section, option, value in settings_lst:
            self.settings.set(section, option, value)
        self.settings.set('FileList', 'SortOrder', self.model.container.sort_order)
        #TODO: (3,2) Improve: make favorites save in the config automatically
        self.model.favorites.save(self.settings)
        self.settings.save()
        self.temp_dir.rmtree(ignore_errors=True)
        log.shutdown()
        
    def on_request_temp_path(self, message):
        import random
        filename = ''.join(random.choice(string.ascii_lowercase) for i in xrange(8))
        message.data.temp_path = self.temp_dir / filename
        message.data.temp_dir = self.temp_dir
            
    @property
    def localization_path(self):
        return self.program_path / u'localization'
    
    @property
    def program_path(self):
        if util.is_frozen():
            return util.get_exe_path().dirname()
        else:
            return self.main_script.dirname()
    
    def can_save_settings_locally(self):
        settings_path = self.program_path / self.INI_FILE_NAME
        try:
            if settings_path.exists():
                with settings_path.open(mode='a') as f:
                    pass
            else:
                return False
        except:
            return False
        return True
    
    def set_settings_location(self, local):
        if local:
            settings_path = self.program_path / self.INI_FILE_NAME
            try:
                if not settings_path.exists():
                    with settings_path.open(mode='w') as f:
                        pass
                    self.settings.path = settings_path
            except:
                pass
        else:
            settings_path = self.program_path / self.INI_FILE_NAME
            try:
                settings_path.remove()
                settings_path = Path(wx.StandardPaths.Get().GetUserDataDir()) / self.INI_FILE_NAME
                self.settings.path = settings_path
            except:
                pass
                
    @staticmethod
    def _get_start_dir(settings):
        start_dir_str = settings.get('Options', 'StartDir')
        start_dir = None
        if start_dir_str:
            start_dir = Path(start_dir_str)
            try:
                if not start_dir.isdir():
                    start_dir = None
            except Exception:
                log.debug(traceback.format_exc())
                start_dir = None
        if not start_dir:
            start_dir = Path(wx.StandardPaths.Get().GetDocumentsDir())
        return start_dir
    
    @staticmethod
    def _get_temp_dir():
        import tempfile
        temp_dir = tempfile.mkdtemp(prefix='quivi_')
        try:
            return Path(temp_dir)
        except UnicodeDecodeError:
            return Path(unicode(temp_dir, 'mbcs'))
