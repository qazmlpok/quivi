

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
from quivilib.model.favorites import Favorite
from pathlib import Path
from quivilib import util

import quivilib.tempdir as tempdir

import wx
from pubsub import pub as Publisher

import string
import logging as log
import traceback
import sys



class MainController(object):
    #TODO: (1,3) Refactor: move 'favorites.changed' events to the model?
    
    
    INI_FILE_NAME = 'pyquivi.ini'
    LOG_FILE_NAME = 'quivi.log' 
    STDIO_FILE_NAME = 'error.log' 
    
    def __init__(self, main_script, file_to_open):
        if main_script is not None:
            self.main_script = Path(main_script)
        wx.GetApp().SetAppName(meta.APPNAME)
        
        try:
            userdatadir = Path(wx.StandardPaths.Get().GetUserDataDir())
            if not userdatadir.is_dir():
                userdatadir.mkdir()
        except:
            pass
        
        if meta.DEBUG:
            log.basicConfig(encoding='utf8')
            log_file = Path(wx.StandardPaths.Get().GetUserDataDir()) / self.LOG_FILE_NAME
            fh = log.FileHandler(log_file, mode='w', encoding='utf8')
            fh.setLevel(meta.LOG_LEVEL)
            log.getLogger().addHandler(fh)
        else:
            log_file = Path(wx.StandardPaths.Get().GetUserDataDir()) / self.LOG_FILE_NAME
            log.basicConfig(filename=log_file, filemode='w', encoding='utf8')
        log.getLogger().setLevel(meta.LOG_LEVEL)
        
        wx.ArtProvider.Push(QuiviArtProvider())
        
        if self.can_save_settings_locally():
            settings_path = self.program_path / self.INI_FILE_NAME
            stdio_path = self.program_path / self.STDIO_FILE_NAME
        else:
            settings_path = Path(wx.StandardPaths.Get().GetUserDataDir()) / self.INI_FILE_NAME
            stdio_path = Path(wx.StandardPaths.Get().GetUserDataDir()) / self.STDIO_FILE_NAME
        Publisher.subscribe(self.on_settings_corrupt, 'settings.corrupt')
        self.settings = Settings(settings_path)
        start_dir = self._get_start_dir(self.settings)
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
        Publisher.sendMessage('favorites.changed', favorites=self.model.favorites)
        Publisher.sendMessage('settings.loaded', settings=self.model.settings)
        
        #Receive messages for Settings from the Daemon thread
        Publisher.subscribe(self.on_update_available, 'program.update_available')
        Publisher.subscribe(self.on_no_update_available, 'program.no_update_available')
        
        self.pane_info = None
        
        if file_to_open:
            self.file_list.open_path(file_to_open)
            
        self.update_checker = UpdateChecker(self.settings)
        
    def quit(self):
        self.view.Close()
        
    def toggle_fullscreen(self):
        UseRealFullscreen = self.settings.get('Options', 'RealFullscreen') == '1'
        if UseRealFullscreen:
            style = wx.FULLSCREEN_ALL
        else:
            style = (wx.FULLSCREEN_NOBORDER | wx.FULLSCREEN_NOCAPTION)
        self.view.ShowFullScreen(not self.view.IsFullScreen(), style)
    
    def MaybeMaximize(self):
        """
        Set the MainWindow to fullscreen if the app was in fullscreen when last closed
        This has to be done after Show() or the app gets messed up badly.
        This used to be the case for Maximized, but maybe that was fixed.
        """
        useFullscreen = self.settings.getboolean('Window', 'MainWindowFullscreen')
        autoFullscreen = self.settings.getboolean('Options', 'AutoFullscreen')
        if useFullscreen and autoFullscreen:
            self.toggle_fullscreen()
        
    def on_update_fullscreen_menu_item(self, event):
        event.Check(self.view.IsFullScreen())
        
    def toggle_file_list(self):
        #TODO: *(2,?) Fix: panel is not always restored with its previous size.
        #      Ask wxPython people?
        pane = self.view.aui_mgr.GetPane('file_list')
        if pane.IsShown():
            pane.BestSize(self.view.file_list_panel.GetSize())
        show = not pane.IsShown() 
        pane.Show(show)
        self.view.aui_mgr.Update()
        
    def on_update_file_list_menu_item(self, event):
        pane = self.view.aui_mgr.GetPane('file_list')
        event.Check(pane.IsShown())
        
    def on_update_image_available_menu_item(self, event):
        event.Enable(self.model.canvas.has_image())
        
    def toggle_thumbnails(self):
        pane = self.view.file_list_panel
        pane.toggle_thumbnails()
    
    def on_update_thumbnail_menu_item(self, event):
        pane = self.view.file_list_panel
        event.Check(pane.is_thumbnails())
        
    def add_favorite(self):
        path = self.model.container.universal_path
        if path:
            favorite = Favorite(path, None, None)
            self.model.favorites.insert(favorite)
            Publisher.sendMessage('favorites.changed', favorites=self.model.favorites)
            Publisher.sendMessage('favorite.opened', favorite=True)
    def add_placeholder(self):
        """
        Like favorites, but 1. includes the current page
        2. Adding a new placeholder for the same object will replace the previous placeholder
        3. Placeholders are intended to be temporary and may be automatically deleted on load
           or on saving a placeholder for any other item. There are settings to control this.
        """
        path = self.model.container.universal_path
        if path:
            idx = self.model.container.selected_item_index
            filename = self.model.container.items[idx].namebase
            placeholder = Favorite(path, idx, filename)
            self.model.favorites.insert(placeholder)
            autodelete = self.settings.get('Options', 'PlaceholderSingle') == '1'
            if autodelete:
                #Look for a placeholder for any other container and delete it/them
                favs = self.model.favorites.getitems()
                for (k, fav) in favs:
                    if fav.is_placeholder() and fav.path != path:
                        log.debug(f"Remove existing placeholder: {fav.path}")
                        self.model.favorites.remove(fav.path, True)
            Publisher.sendMessage('favorites.changed', favorites=self.model.favorites)
        
        
    def remove_favorite(self):
        self.model.favorites.remove(self.model.container.path, False)
        Publisher.sendMessage('favorites.changed', favorites=self.model.favorites)
        Publisher.sendMessage('favorite.opened', favorite=False)
    
    def remove_placeholder(self):
        self.model.favorites.remove(self.model.container.path, True)
        Publisher.sendMessage('favorites.changed', favorites=self.model.favorites)
    
    def copy_to_clipboard(self):
        self.model.canvas.copy_to_clipboard()
        
    def delete(self):
        self.file_list.delete(self.view)
        
    def open_about_dialog(self):
        Publisher.sendMessage('about.open_dialog')
        
    def open_help(self):
        import webbrowser
        webbrowser.open(meta.HELP_URL)
        
    def open_feedback(self):
        import webbrowser
        webbrowser.open(meta.REPORT_URL)
        
    def on_open_update_site(self, *, url):
        import webbrowser
        webbrowser.open(url)
        
    def on_program_closed(self, *, settings_lst=None):
        for section, option, value in settings_lst:
            self.settings.set(section, option, value)
        self.settings.set('FileList', 'SortOrder', self.model.container.sort_order)
        #TODO: (3,2) Improve: make favorites save in the config automatically
        self.model.favorites.save(self.settings)
        self.settings.save()
        tempdir.delete_tempdir()
        log.shutdown()

    def on_update_available(self, *, down_url, check_time, version):
        self.settings.set('Update', 'Available', '1')
        if check_time is not None:
            self.settings.set('Update', 'URL', down_url)
            self.settings.set('Update', 'LastCheck', check_time)
            self.settings.set('Update', 'Version', version)

    def on_no_update_available(self, *, check_time):
        self.settings.set('Update', 'Available', '0')
        if check_time is not None:
            self.settings.set('Update', 'LastCheck', check_time)

    def on_settings_corrupt(self, *, backupFilename):
        import wx
        from quivilib.i18n import _
        if backupFilename is not None:
            msg = _('The settings file is corrupt and cannot be opened. Settings will return to their default values. The corrupt file has been renamed to %s.') % backupFilename
        else:
            msg = _('The settings file is corrupt and cannot be opened. Settings will return to their default values.')
        #Self.view won't exist when this is called.
        def fn():
            #This honestly looks awful, but ideally it won't ever be displayed, so I'm not concerned.
            dlg = wx.MessageDialog(self.view, msg, _('Settings lost'), wx.OK | wx.ICON_WARNING)
            dlg.ShowModal()
            dlg.Destroy()
        wx.CallLater(1, fn)

    @property
    def localization_path(self):
        return self.program_path / 'localization'
    
    @property
    def program_path(self):
        if util.is_frozen():
            return util.get_exe_path().parent
        else:
            return self.main_script.parent
    
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
                if not start_dir.is_dir():
                    start_dir = None
            except Exception:
                log.debug(traceback.format_exc())
                start_dir = None
        if not start_dir:
            start_dir = Path(wx.StandardPaths.Get().GetDocumentsDir())
        return start_dir

