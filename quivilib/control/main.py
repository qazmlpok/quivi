import sys
from pathlib import Path
import logging as log
import traceback

import wx
from pubsub import pub as Publisher

from quivilib import meta
from quivilib.i18n import _
from quivilib.model import App
from quivilib.model.container import ItemType
from quivilib.model.settings import Settings
from quivilib.gui.main import MainWindow
from quivilib.gui.art import QuiviArtProvider 
from quivilib.control.file_list import FileListController
from quivilib.control.menu import MenuController
from quivilib.control.canvas import CanvasController
from quivilib.control.wallpaper import WallpaperController
from quivilib.control.options import OptionsController
from quivilib.control.debug import DebugController
from quivilib.control.cache import ImageCache
from quivilib.control.check_update import UpdateChecker
from quivilib.control.i18n import I18NController
from quivilib.model.favorites import Favorite
from quivilib import util
from quivilib import tempdir


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
        
        self.i18n = I18NController(self, self.settings)
        self.cache = ImageCache(self.settings)
        self.canvas = CanvasController('canvas', self.view.canvas_view, settings=self.settings)
        #This will send messages due to opening the default container
        #TODO: Probably should move that out of the constructor...
        self.file_list = FileListController(self.model, self.model.container)
        self.wallpaper = WallpaperController(self.model)
        self.options = OptionsController(self, self.model)
        
        self.debugController = None
        if __debug__:
            self.debugController = DebugController(self.model)
        
        #This must be the last controller created (it references the others)
        self.menu = MenuController(self, self.settings)
        
        Publisher.subscribe(self.on_program_closed, 'program.closed')
        Publisher.subscribe(self.on_open_update_site, 'program.open_update_site')
        Publisher.sendMessage('favorites.changed', favorites=self.model.favorites, settings=self.model.settings)
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
        
    def toggle_spread(self):
        using_feature = self.settings.get('Options', 'DetectSpreads') == '1'
        #Invert the boolean and convert to str
        self.settings.set('Options', 'DetectSpreads', '0' if using_feature else '1')
        #This will reset zoom even if it isn't a spread - worth checking?
        self.canvas.set_zoom_by_current_fit()
    
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
        
    def on_update_file_list_menu_item(self, event: wx.UpdateUIEvent):
        pane = self.view.aui_mgr.GetPane('file_list')
        event.Check(pane.IsShown())
        
    def on_update_spread_toggle_menu_item(self, event: wx.UpdateUIEvent):
        using_feature = self.settings.get('Options', 'DetectSpreads') == '1'
        event.Check(using_feature)
        
    def on_update_image_available_menu_item(self, event: wx.UpdateUIEvent):
        event.Enable(self.canvas.has_image())
        
    def toggle_thumbnails(self):
        pane = self.view.file_list_panel
        pane.toggle_thumbnails()
    
    def on_update_thumbnail_menu_item(self, event: wx.UpdateUIEvent):
        pane = self.view.file_list_panel
        event.Check(pane.is_thumbnails())
        
    def add_favorite(self):
        path = self.model.container.universal_path
        if path:
            favorite = Favorite(path, None, None)
            self.model.favorites.insert(favorite)
            Publisher.sendMessage('favorites.changed', favorites=self.model.favorites, settings=self.model.settings)
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
            Publisher.sendMessage('favorites.changed', favorites=self.model.favorites, settings=self.model.settings)

    def remove_favorite(self):
        self.model.favorites.remove(self.model.container.path, False)
        Publisher.sendMessage('favorites.changed', favorites=self.model.favorites, settings=self.model.settings)
        Publisher.sendMessage('favorite.opened', favorite=False)
    
    def remove_placeholder(self):
        self.model.favorites.remove(self.model.container.path, True)
        Publisher.sendMessage('favorites.changed', favorites=self.model.favorites, settings=self.model.settings)
    
    def open_latest_placeholder(self):
        for fav in reversed(self.model.favorites.ordered_items()):
            if fav.is_placeholder():
                Publisher.sendMessage('favorite.open', favorite=fav, window=None)
                break

    def copy_to_clipboard(self):
        self.canvas.copy_to_clipboard()
    def copy_path_to_clipboard(self):
        if wx.TheClipboard.Open():
            wx.TheClipboard.SetData(wx.TextDataObject(str(self.model.container.path)))
            #Keep data available even after application close.
            wx.TheClipboard.Flush()
            wx.TheClipboard.Close()
        
    def delete(self):
        """ Calls either delete_container or delete_image depends on whether a zip file or directory is open."""
        container = self.model.container
        if container.can_delete_self():
            self.delete_container(False)
        elif container.can_delete_contents():
            self.delete_image(False)
        #Else, do nothing. _can_delete should have returned false.

    def delete_container(self, direct=True):
        """ Delete the currently opened archive file.
         The `direct` parameter is true if this was called directly via command, false if called by `delete`. This only affects messaging.
         """
        container = self.model.container
        if not container.can_delete_self():
            if direct:
                #Only show a message if this is a direct command invocation.
                dlg = wx.MessageDialog(self.view, _('The file was not deleted as this is not supported for directories'),
                                       _("File not deleted"), wx.OK)
                dlg.ShowModal()
                dlg.Destroy()
            return
        if not self._ask_delete_confirmation(self.view, container.name):
            return
        self.canvas.close_img()
        self.file_list.open_parent()
        container.delete_self(self.view)
        Publisher.sendMessage("cache.flush")

    def delete_image(self, direct=True):
        """ Deletes the currently opened image. Only works when viewing a directory of images - there's no attempt to modify zip archives.
        The `direct` parameter is true if this was called directly via command, false if called by `delete`. This only affects messaging.
        """
        container = self.model.container
        if not container.can_delete_contents():
            if direct:
                #Only show a message if this is a direct command invocation.
                dlg = wx.MessageDialog(self.view, _('The file was not deleted as this is not supported for zip archives'),
                                       _("File not deleted"), wx.OK)
                dlg.ShowModal()
                dlg.Destroy()
            return

        index = self.model.container.selected_item_index
        filetype = self.model.container.items[index].typ
        if not self._ask_delete_confirmation(self.view, container.get_item_name(index)):
            return
        #Release any handle on the file...
        img = self.canvas.get_img()
        if filetype == ItemType.IMAGE and img:
            img.close()
        container.delete_image(index, self.view)
        self.file_list.refresh_after_delete(index)

    def _need_delete_confirmation(self):
        # No confirmation on win32 because it uses the recycle bin.
        # TODO: Linux can trash items via `gio trash`. If the command is available, use it.
        return (sys.platform != 'win32')
    def _ask_delete_confirmation(self, window, path: str):
        if not self._need_delete_confirmation():
            return True
        dlg = wx.MessageDialog(window, _('Are you sure you want to delete "%s"?') % path,
                               _("Confirm file deletion"), wx.YES_NO | wx.ICON_QUESTION)
        res = dlg.ShowModal()
        dlg.Destroy()
        return res == wx.ID_YES

    def on_update_delete_menu_item(self, event):
        """ Enables/Disables the "delete" menu item. """
        event.Enable(self._can_delete())

    def _can_delete(self):
        container = self.model.container
        return container.can_delete_self() or container.can_delete_contents()

    def open_move_dialog(self):
        if not self.model.container.can_move:
            return
        #Nested virtual containers can't be moved, so a single parent is always fine.
        start_path = str(self.model.container.path.parent)
        Publisher.sendMessage(
            'movefile.open_dialog',
            settings=self.settings,
            name=self.model.container.name,
            start_path=start_path
        )
    def open_about_dialog(self):
        Publisher.sendMessage('about.open_dialog')
        
    def open_help(self):
        import webbrowser
        webbrowser.open(meta.HELP_URL)
        
    def open_feedback(self):
        import webbrowser
        webbrowser.open(meta.REPORT_URL)
        
    def open_debug_cache_dialog(self):
        if __debug__:
            self.debugController.open_debug_cache_dialog()
    def open_debug_memory_dialog(self):
        if __debug__:
            self.debugController.open_debug_memory_dialog()
        
    def on_open_update_site(self, *, url):
        import webbrowser
        if url is not None:
            webbrowser.open(url)

    def check_updates(self):
        #Debug method - clear the saved timestamp. An actual command to "Check for updates" would be more useful.
        #But it's not like this program gets updated...
        if __debug__:
            self.settings.set('Update', 'LastCheck', '')
        
    def open_context_menu(self):
        Publisher.sendMessage('menu.context_menu')
        
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
