
from quivilib.control.options import get_fit_choices
from quivilib.meta import PATH_SEP

import wx
import wx.aui
from pubsub import pub as Publisher

from quivilib.i18n import _
from quivilib import meta
from quivilib.util import error_handler
from quivilib.gui.file_list import FileListPanel
from pathlib import Path
from quivilib.resources import images
from quivilib import util

import traceback
import logging as log

ZOOM_FIELD = 2
SIZE_FIELD = 1
FIT_FIELD = 3



def _handle_error(exception, args, kwargs):
    self = args[0]
    self.handle_error(exception)
    


#class MainWindow(wx.Frame, wx.FileDropTarget):
class MainWindow(wx.Frame):

    def __init__(self):
        wx.Frame.__init__(self, parent=None, id=-1, title=meta.APPNAME)
        self.aui_mgr = wx.aui.AuiManager()
        self.aui_mgr.SetManagedWindow(self)
        self.aui_mgr.SetFlags(self.aui_mgr.GetFlags()
                              & ~wx.aui.AUI_MGR_ALLOW_ACTIVE_PANE)
        
        bundle = wx.IconBundle()
        bundle.AddIcon(images.quivi16.Icon)
        bundle.AddIcon(images.quivi32.Icon)
        bundle.AddIcon(images.quivi48.Icon)
        bundle.AddIcon(images.quivi256.Icon)
        self.SetIcons(bundle)
        
        dt = self.QuiviFileDropTarget(self)
        self.SetDropTarget(dt)
        
        self.menu_bar = wx.MenuBar()
        self.SetMenuBar(self.menu_bar)
        
        self.status_bar = wx.StatusBar(self)
        self.SetStatusBar(self.status_bar)
        self.status_bar.SetFieldsCount(4)
        size_width = self.status_bar.GetTextExtent('10000 x 10000')[0] + 10
        zoom_width = self.status_bar.GetTextExtent('9999.99%')[0] + 20
        fit_width = self.status_bar.GetTextExtent('Width if larger with added stuff')[0] + 20
        self.status_bar.SetStatusWidths([-1, size_width, zoom_width, fit_width])
        
        self.file_list_panel = FileListPanel(self)
        self.aui_mgr.AddPane(self.file_list_panel, wx.aui.AuiPaneInfo().
                             Name('file_list').Caption(_('Files')).Left().
                             Layer(1).Position(0).CloseButton(True).
                             DestroyOnClose(False).BestSize((300, 400)))
        
        self.panel = wx.Panel(self)
        self.panel.SetBackgroundStyle(wx.BG_STYLE_COLOUR)
        self.aui_mgr.AddPane(self.panel, wx.aui.AuiPaneInfo().Name("content").
                             CenterPane())
        
        self.aui_mgr.Update()
        
        self.panel.Bind(wx.EVT_PAINT, self.on_panel_paint)
        self.panel.Bind(wx.EVT_MOUSEWHEEL, self.on_mouse_wheel)
        self.panel.Bind(wx.EVT_ENTER_WINDOW, self.on_mouse_enter)
        self._bind_panel_mouse_events()
        self.panel.Bind(wx.EVT_MOTION, self.on_mouse_motion)
        self.Bind(wx.EVT_SIZE, self.on_resize)
        self.Bind(wx.EVT_MOVE, self.on_move)
        self.Bind(wx.EVT_CLOSE, self.on_close)
        self.status_bar.Bind(wx.EVT_CONTEXT_MENU, self.on_fit_context_menu)
        
        Publisher.subscribe(self.on_busy, 'busy')
        Publisher.subscribe(self.on_error, 'error')
        Publisher.subscribe(self.on_freeze, 'gui.freeze')
        Publisher.subscribe(self.on_thaw, 'gui.thaw')
        Publisher.subscribe(self.on_selection_changed, 'container.selection_changed')
        Publisher.subscribe(self.on_container_opened, 'container.opened')
        Publisher.subscribe(self.on_image_opened, 'container.image.opened')
        Publisher.subscribe(self.on_image_loading, 'container.image.loading')
        Publisher.subscribe(self.on_image_loaded, 'canvas.image.loaded')
        Publisher.subscribe(self.on_language_changed, 'language.changed')
        Publisher.subscribe(self.on_canvas_changed, 'canvas.changed')
        Publisher.subscribe(self.on_canvas_fit_changed, 'canvas.fit.changed')
        Publisher.subscribe(self.on_canvas_cursor_changed, 'canvas.cursor.changed')
        Publisher.subscribe(self.on_canvas_zoom_changed, 'canvas.zoom.changed')
        Publisher.subscribe(self.on_menu_built, 'menu.built')
        Publisher.subscribe(self.on_menu_labels_changed, 'menu.labels.changed')
        Publisher.subscribe(self.on_favorites_changed, 'favorites.changed')
        Publisher.subscribe(self.on_settings_loaded, 'settings.loaded')
        Publisher.subscribe(self.on_open_wallpaper_dialog, 'wallpaper.open_dialog')
        Publisher.subscribe(self.on_open_options_dialog, 'options.open_dialog')
        Publisher.subscribe(self.on_open_about_dialog, 'about.open_dialog')
        Publisher.subscribe(self.on_open_directory_dialog, 'file_list.open_directory_dialog')
        Publisher.subscribe(self.on_update_available, 'program.update_available')
        Publisher.subscribe(self.on_bg_color_changed, 'settings.loaded')
        Publisher.subscribe(self.on_bg_color_changed, 'settings.changed.Options.CustomBackground')
        Publisher.subscribe(self.on_bg_color_changed, 'settings.changed.Options.CustomBackgroundColor')
        Publisher.subscribe(self.on_canvas_fit_changed, 'settings.loaded')
        Publisher.subscribe(self.on_canvas_fit_changed, 'settings.changed.Options.FitType')
        Publisher.subscribe(self.on_canvas_fit_changed, 'settings.changed.Options.FitWidthCustomSize')
        
        self._last_size = self.GetSize() 
        self._last_pos = self.GetPosition()
        self._busy = False
        #List of (id, name) tuples. Filled on the favorites.changed event,
        #used in the file list popup menu
        self.favorites_menu_items = []
        self.update_menu_item = None
        #Track as a dictionary
        self.menus = {}
        
    def _bind_panel_mouse_events(self):
        def make_fn(button_idx, event_idx):
            def fn(event):
                Publisher.sendMessage('canvas.mouse.event', button=button_idx, event=event_idx)
                event.Skip()
            return fn
        for button_idx, button in enumerate(('LEFT', 'MIDDLE', 'RIGHT')):
            for event_idx, event in enumerate(('DOWN', 'UP')):
                eid = getattr(wx, f'EVT_{button}_{event}')
                self.panel.Bind(eid, make_fn(button_idx, event_idx))
    
    @property
    def canvas_view(self):
        class CanvasAdapter(object):
            def __init__(self, panel):
                self.panel = panel
            
            @property
            def width(self):
                return self.panel.GetSize()[0]
            
            @property
            def height(self):
                return self.panel.GetSize()[1]

        return CanvasAdapter(self.panel)
    
    def save(self, settings_lst):
        perspective = self.aui_mgr.SavePerspective()
        settings_lst.append(('Window', 'Perspective', perspective))
        settings_lst.append(('Window', 'MainWindowX', self._last_pos[0]))
        settings_lst.append(('Window', 'MainWindowY', self._last_pos[1]))
        settings_lst.append(('Window', 'MainWindowWidth', self._last_size[0]))
        settings_lst.append(('Window', 'MainWindowHeight', self._last_size[1]))
        settings_lst.append(('Window', 'MainWindowMaximized', '1' if self.IsMaximized() else '0'))
    
    def load(self, settings):
        perspective = settings.get('Window', 'Perspective')
        if perspective:
            self.aui_mgr.LoadPerspective(perspective)
        width = max(settings.getint('Window', 'MainWindowWidth'), 200)
        height = max(settings.getint('Window', 'MainWindowHeight'), 200)
        x = max(settings.getint('Window', 'MainWindowX'), 0)
        y = max(settings.getint('Window', 'MainWindowY'), 0)
        self.SetSize(x, y, width, height)
        self.Maximize(settings.getboolean('Window', 'MainWindowMaximized'))
        if wx.Display.GetFromWindow(self) == wx.NOT_FOUND:
            self.SetSize(0, 0, width, height)
    
    def on_resize(self, event):
        Publisher.sendMessage('canvas.resized')
        if not self.IsMaximized():
            self._last_size = self.GetSize()
            
    def on_move(self, event):
        if not self.IsMaximized():
            self._last_pos = self.GetPosition()
        
    @error_handler(_handle_error)
    def on_close(self, event):
        settings_lst = []
        self.save(settings_lst)
        self.file_list_panel.save(settings_lst)
        try:
            Publisher.sendMessage('program.closed', settings_lst=settings_lst)
        except Exception:
            log.error(traceback.format_exc())
        
        self.aui_mgr.UnInit()
        del self.aui_mgr
        self.Destroy()
        
    def on_mouse_motion(self, event):
        Publisher.sendMessage('canvas.mouse.motion', x=event.GetX(), y=event.GetY())
        event.Skip()
        
    def on_settings_loaded(self, *, settings):
        self.load(settings)
        self.file_list_panel.load(settings)
    
    def on_panel_paint(self, event):
        if meta.DOUBLE_BUFFERING:
            dc = wx.BufferedPaintDC(self.panel)
        else:
            dc = wx.PaintDC(self.panel)
        #This is required on Linux
        dc.SetBackground(wx.Brush(self.panel.GetBackgroundColour()))
        dc.Clear()
        class PaintedRegion(object):
            pass
        painted_region = PaintedRegion()
        Publisher.sendMessage('canvas.painted', dc=dc, painted_region=painted_region)
        clip_region = wx.Region(0, 0, self.panel.GetSize()[0],
                                self.panel.GetSize()[1])
        clip_region.Subtract(wx.Rect(painted_region.left, painted_region.top,
                                     painted_region.width, painted_region.height))
        #Fix for bug in Linux (without this it would clear the entire image
        #when the panel is smaller than the image
        iter = wx.RegionIterator(clip_region)
        if iter and not meta.DOUBLE_BUFFERING:
            dc.SetClippingRegionAsRegion(clip_region)
            dc.Clear()
        
    def on_mouse_wheel(self, event):
        lines = event.GetWheelRotation() / event.GetWheelDelta()
        lines *= event.GetLinesPerAction()
        Publisher.sendMessage('canvas.scrolled', lines=lines)
        
    def on_mouse_enter(self, event):
        self.panel.SetFocus()
        
    def on_fit_context_menu(self, event):
        menu = wx.Menu()
        #I can't figure out how to test this. Is this reachable?
        self.PopupMenu(self.menus['Fit'])
        menu.Destroy()
        
    def on_busy(self, *, busy):
        if self._busy == busy:
            return
        if busy:
            wx.BeginBusyCursor()
        else:
            #Fix for a bizarre bug that would deadlock the app on Linux
            wx.CallAfter(wx.EndBusyCursor)
        self._busy = busy
        
    def on_freeze(self):
        self.Freeze()
        
    def on_thaw(self):
        self.Thaw()
    
    def on_error(self, *, exception, tb):
        self.handle_error(exception, tb)
        
    def on_canvas_changed(self):
        self.panel.Refresh(eraseBackground=False)
        
    def on_canvas_fit_changed(self, *, settings=None, FitType=None):
        #Using the same listener for two different messages,
        #so parse it differently
        if FitType is not None:
            fit_type = FitType
        else:
            fit_type = settings.getint('Options', 'FitType')
        fit_choices = get_fit_choices()
        name = [name for name, typ in fit_choices if typ == fit_type][0]
        self.status_bar.SetStatusText(name, FIT_FIELD)
        
    def on_canvas_cursor_changed(self, *, cursor):
        self.panel.SetCursor(cursor)
        
    def on_canvas_zoom_changed(self, *, zoom):
        text = util.get_formatted_zoom(zoom)
        self.status_bar.SetStatusText(text, ZOOM_FIELD)
        
    def on_menu_built(self, *, main_menu):
        for category in main_menu:
            menu = self._make_menu(category.commands)
            self.menu_bar.Append(menu, category.name)
        #Remove the hidden menus.
        #It is removed from the menu bar but a reference to it is kept
        #in order to keep its keyboard shortcuts working
        for category in main_menu:
            #https://stackoverflow.com/questions/27662721/removing-a-menu-from-a-wxpython-menubar
            menu_pos = self.menu_bar.FindMenu(category.name)
            if menu_pos >= 0:
                self.menus[category.clean_name] = self.menu_bar.GetMenu(menu_pos)
            if category.hidden and menu_pos >= 0:
                self.menu_bar.Remove(menu_pos)
            
    def _make_menu(self, commands):
        menu = wx.Menu()
        for command in commands:
            if command:
                def event_fn(event, cmd=command):
                    try:
                        cmd()
                    except Exception as e:
                        self.handle_error(e)
                style = wx.ITEM_CHECK if command.checkable else wx.ITEM_NORMAL
                menu.Append(command.ide, command.name_and_shortcut, command.description, style)
                self.Bind(wx.EVT_MENU, event_fn, id=command.ide)
                if command.update_function:
                    wx.GetApp().Bind(wx.EVT_UPDATE_UI, command.update_function, id=command.ide)
            else:
                menu.AppendSeparator()
        return menu
    
    def on_favorites_changed(self, *, favorites):
        favorites_menu = self.menus['Favorites']
        
        #TODO: (1,2) Improve: likewise, 3 is the number of submenus in the favorites menu;
        #      entries bigger than 3 are the favorites themselves.
        while favorites_menu.GetMenuItemCount() > 2:
            menu = favorites_menu.FindItemByPosition(2)
            favorites_menu.Delete(menu)
        items = favorites.getitems()
        if items:
            favorites_menu.AppendSeparator()
        self.favorites_menu_items = []
        i = 0
        for path_key, path in items:
            ide = wx.NewId()
            def event_fn(event, favorite=path):
                try:
                    Publisher.sendMessage('favorite.open', favorite=favorite)
                except Exception as e:
                    self.handle_error(e)
            #In path for drives (e.g. D:\), name is '' 
            if path.name == '':
                name = path
            else:
                name = path.name
            #Handle universal path names
            name = name.split(PATH_SEP)[-1]
            #Prevents incorrect shortcut definition
            name = name.replace('&', '&&')
            if not name:
                continue
            favorites_menu.Append(ide, name)
            self.favorites_menu_items.append((ide, name))
            self.Bind(wx.EVT_MENU, event_fn, id=ide)
            i += 1

    def on_menu_labels_changed(self, *, main_menu, commands, accel_table):
        self.accel_table = accel_table
        self.SetAcceleratorTable(self.accel_table)
        for cmd in commands:
            menu_item = self.menu_bar.FindItemById(cmd.ide)
            if menu_item is not None:
                menu_item.SetItemLabel(cmd.name_and_shortcut)
                menu_item.SetHelp(cmd.description)
        for idx, category in enumerate(main_menu):
            if not category.hidden:
                #Get the actual index of the menu, not what the array specifies.
                #This allows putting hidden images before visible ones.
                idx = self.menu_bar.FindMenu(category.name)
                self.menu_bar.SetMenuLabel(idx, category.name)
    
    def on_container_opened(self, *, container):
        self.SetTitle(f'{container.name} - {meta.APPNAME}')
        self.status_bar.SetStatusText(container.name)
    
    def on_image_opened(self, *, item):
        self.SetTitle(f'{item.name} - {meta.APPNAME}')
        self.status_bar.SetStatusText(str(item.full_path))
        
    def on_image_loading(self, *, item):
        self.status_bar.SetStatusText(_('Loading...'))
        
    def on_image_loaded(self, *, width, height):
        self.status_bar.SetStatusText('%d x %d' % (width, height), SIZE_FIELD)
    
    def on_selection_changed(self, *, idx, item):
        self.status_bar.SetStatusText(str(item.full_path))
    
    def on_language_changed(self):
        self.aui_mgr.GetPane('file_list').Caption(_('Files'))
        self.aui_mgr.Update()
        if self.update_menu_item:
            self.update_menu_item.SetItemLabel(_('&Download'))
            self.update_menu_item.SetHelp(_('Go to the download site'))
            self.menu_bar.SetMenuLabel(self.menu_bar.GetMenuCount()-1,
                                       _('&New version available!'))
    
    def on_open_wallpaper_dialog(self, *, choices, color):
        from quivilib.gui.wallpaper import WallpaperDialog
        dialog = WallpaperDialog(self, choices, color)
        dialog.ShowModal()
        dialog.Destroy()
        
    def on_open_options_dialog(self, *, fit_choices, settings, categories, available_languages, active_language, save_locally):
        from quivilib.gui.options import OptionsDialog
        dialog = OptionsDialog(self, fit_choices, settings, categories, available_languages, active_language, save_locally)
        dialog.ShowModal()
        dialog.Destroy()
        
    def on_open_directory_dialog(self, *, req):
        dialog = wx.DirDialog(self, _('Choose a directory:'),
                              style=wx.DD_DEFAULT_STYLE|wx.DD_DIR_MUST_EXIST)
        dialog.SetPath(str(req.start_directory))
        if dialog.ShowModal() == wx.ID_OK:
            req.directory = Path(dialog.GetPath())
        dialog.Destroy()
        
    def on_open_about_dialog(self):
        from quivilib.gui.about import AboutDialog
        dialog = AboutDialog(self)
        dialog.ShowModal()
        dialog.Destroy()
        
    def on_update_available(self, *, down_url):
        menu = wx.Menu()
        ide = wx.NewId()
        self.update_menu_item = menu.Append(ide, _('&Download'), _('Go to the download site'))
        self.menu_bar.Append(menu, _('&New version available!'))
        def event_fn(event):
            Publisher.sendMessage('program.open_update_site', url=down_url)
        self.Bind(wx.EVT_MENU, event_fn, id=ide)
        
    def on_bg_color_changed(self, *, settings):
        if settings.get('Options', 'CustomBackground') == '1':
            color = settings.get('Options', 'CustomBackgroundColor').split(',')
            color = wx.Colour(*[int(c) for c in color])
        else:
            color = wx.SystemSettings.GetColour(wx.SYS_COLOUR_APPWORKSPACE)
        self.panel.SetBackgroundColour(color)
        self.panel.Refresh()

    def handle_error(self, exception, tb=None):
        from quivilib.gui.error import ErrorDialog
        if not tb:
            tb = traceback.format_exc()
        msg, tb = util.format_exception(exception, tb)
        log.error(tb)
        print(tb)##
        def fn():
            dlg = ErrorDialog(parent=self, error=msg, tb=tb)
            dlg.ShowModal()
            dlg.Destroy()
        #TODO: (2,?) Investigate
        #This is a workaround for a bizarre bug in wx.
        wx.CallLater(400, fn)

    
    class QuiviFileDropTarget(wx.FileDropTarget):
        def __init__(self, window):
            wx.FileDropTarget.__init__(self)

        @error_handler(_handle_error)
        def OnDropFiles(self, x, y, filenames):
            filename = filenames[0]
            path = Path(filename)
            Publisher.sendMessage('file.dropped', path=path)
            return True
