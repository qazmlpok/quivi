

#TODO: (2,3) Refactor: this module and classes were poorly named.
#    this is actually about commands, and not the menu.

from quivilib.i18n import _
from quivilib.model.command import Command, CommandCategory
from quivilib.model.shortcut import Shortcut
from quivilib.control import canvas
from quivilib.model.settings import Settings

import wx
from wx.lib.pubsub import pub as Publisher

from functools import partial

SHORTCUTS_KEY = 'Shortcuts'



class MenuController(object):
    def __init__(self, control, settings):
        self.settings = settings
        self.control = control
        self.commands = []
        self.main_menu, self.commands = self._make_commands(self.control)
        self._load_shortcuts(self.settings, self.commands)
        self.shortcuts = self._get_accelerator_table(self.commands)
        #These must be sent in this order
        Publisher.sendMessage('menu.built', self.main_menu)
        Publisher.sendMessage('toolbar.built', self._get_toolbar_commands(self.commands))
        #TODO: (2,2) Refactor: change this message name. This also notifies that
        #    shortcuts have changed.
        Publisher.sendMessage('menu.labels.changed', (self.main_menu, self.commands, self.shortcuts))
        
        Publisher.subscribe(self.on_language_changed, 'language.changed')
        Publisher.subscribe(self.on_command_execute, 'command.execute')
        
    def set_shortcuts(self, shortcuts_dic):
        """Set new shortcuts.
        
        @type shortcuts_dic: dict(Command -> list(Shortcut))
        """
        for cmd, shortcuts in list(shortcuts_dic.items()):
            cmd.shortcuts = shortcuts
        self._save_shortcuts(self.settings, self.commands)
        self.shortcuts = self._get_accelerator_table(self.commands)
        Publisher.sendMessage('menu.labels.changed', (self.main_menu, self.commands, self.shortcuts))
        
    def on_language_changed(self, message):
        self._make_commands(self.control, True)
        Publisher.sendMessage('menu.labels.changed', (self.main_menu, self.commands, self.shortcuts))
        Publisher.sendMessage('toolbar.labels.changed', self._get_toolbar_commands(self.commands))
        
    def on_command_execute(self, message):
        ide = message.data
        [cmd() for cmd in self.commands if cmd.ide == ide]
        
    def _make_commands(self, control, update=False):
        """Make (or update) all commands.
        
        @param control: reference to the main controller instance
        @update: if True, then it will only update the existing commands.
            (Which will retranslate them when changing languages)
        """
        #TODO: (1,2) Refactor: does two different things 
        commands = []
        if update:
            cmd_dict = dict((cmd.ide, cmd) for cmd in self.commands)
            def make(*params, **kwparams):
                ide, name, description = params[0:3]
                cmd_dict[ide].name = name
                cmd_dict[ide].description = description
                return None
            
            def make_category(*params):
                idx, name = params[0:2]
                category = self.main_menu[idx]
                category.name = name
                return None
        else:
            def make(*params, **kwparams):
                params = list(params)
                for idx in range(len(params[4])):
                    params[4][idx] = Shortcut(*params[4][idx])
                command = Command(*params, **kwparams)
                commands.append(command)
                return command
            
            def make_category(*params):
                category = CommandCategory(*params[1:])
                return category
        
        file_menu = (
         make(11001, _('Set as &wallpaper...'), _('Set the opened image as wallpaper'),
              control.wallpaper.open_dialog,
              [(wx.ACCEL_NORMAL, wx.WXK_F3)]),
         make(11002, _('&Copy'), _('Copy the opened image to the clipboard'),
              control.copy_to_clipboard,
              [(wx.ACCEL_CTRL, ord('C'))]),
         make(11004, _('&Delete'), _('Delete the opened image'),
              control.delete,
              [(wx.ACCEL_CTRL, wx.WXK_DELETE)],
              checkable=False, update_function=control.file_list.on_update_delete_menu_item),
         None,
         make(11003, _('&Options...'), _('Open the options dialog'),
              control.options.open_dialog,
              [(wx.ACCEL_NORMAL, wx.WXK_F4)]),
         None,
         make(wx.ID_EXIT, _('&Quit'), _('Close the application'),
              control.quit,
              [])
        )
        folder_menu = (
         make(12001, _('Select/Open &next'), _('Select the next item; if it is an image, show it'),
              partial(control.file_list.select_next, 1),
              [(wx.ACCEL_NORMAL, wx.WXK_END), (wx.ACCEL_NORMAL, wx.WXK_SPACE)]),
         make(12002, _('Select/Open &previous'), _('Select the previous item; if it is an image, show it'),
              partial(control.file_list.select_next, -1),
              [(wx.ACCEL_NORMAL, wx.WXK_HOME)]),
         make(12003, _('Open selected &directory'), _('If a directory or a compressed file is selected, open it'),
              control.file_list.open_selected_container,
              [(wx.ACCEL_NORMAL, wx.WXK_INSERT)]),
         make(12004, _('Open p&arent'), _('Open the parent directory or compressed file'),
              control.file_list.open_parent,
              [(wx.ACCEL_NORMAL, wx.WXK_DELETE)]),
         make(12005, _('Open ne&xt sibling'), _('Open the next directory or compressed file inside the parent'),
              partial(control.file_list.open_sibling, 1),
              [(wx.ACCEL_CTRL, wx.WXK_END)]),
         make(12006, _('Open previou&s sibling'), _('Open the previous directory or compressed file inside the parent'),
              partial(control.file_list.open_sibling, -1),
              [(wx.ACCEL_CTRL, wx.WXK_HOME)]),
         make(12007, _('&Refresh'), _('Refresh the current directory or compressed file; reload the image shown if any'),
              control.file_list.refresh,
              [(wx.ACCEL_NORMAL, wx.WXK_F5)]),
         make(12008, _('Open direc&tory...'), _('Browse for a directory to open'),
              control.file_list.open_directory,
              [(wx.ACCEL_CTRL, ord('O'))])
        )
        view_menu = (
         make(13001, _('Zoom &in'), _('Zoom in'),
              control.canvas.zoom_in,
              [(wx.ACCEL_NORMAL, wx.WXK_NUMPAD_ADD)]),
         make(13002, _('Zoom &out'), _('Zoom out'),
              control.canvas.zoom_out,
              [(wx.ACCEL_NORMAL, wx.WXK_NUMPAD_SUBTRACT)]),
         make(13003, _('&Zoom 100%'), _('Show the image in its real size'),
              control.canvas.zoom_reset,
              [(wx.ACCEL_NORMAL, wx.WXK_NUMPAD_MULTIPLY)]),
         make(13004, _('Fit &width'), _('Zooms the image in order to make its width fit the window'),
              control.canvas.zoom_fit_width,
              [(wx.ACCEL_CTRL, ord('W'))]),
         make(13005, _('Fit &height'), _('Zooms the image in order to make its height fit the window'),
              control.canvas.zoom_fit_height,
              [(wx.ACCEL_CTRL, ord('H'))]),
         make(13008, _('Rotate &clockwise'), _('Rotate the image clockwise'),
              partial(control.canvas.rotate_image, 1),
              [(wx.ACCEL_CTRL, ord('L'))]),
         make(13009, _('Rotate coun&ter clockwise'), _('Rotate the image counter clockwise'),
              partial(control.canvas.rotate_image, 0),
              [(wx.ACCEL_CTRL, ord('K'))]),
         None,
         make(13006, _('&Full screen'), _('Go to/leave full screen mode'),
              control.toggle_fullscreen,
              [(wx.ACCEL_ALT, wx.WXK_RETURN)],
              checkable=True, update_function=control.on_update_fullscreen_menu_item),
         make(13007, _('File &list'), _('Show/hide the file list'),
              control.toggle_file_list,
              [(wx.ACCEL_NORMAL, wx.WXK_TAB)],
              checkable=True, update_function=control.on_update_file_list_menu_item),
         make(13011, _('Thumb&nails'), _('Show/hide the thumbnails'),
              control.toggle_thumbnails,
              [(wx.ACCEL_NORMAL, wx.WXK_F6)],
              checkable=True, update_function=control.on_update_thumbnail_menu_item),
         make(13010, _('Hi&dden files'), _('Show/hide hidden files in the file list'),
              control.file_list.toggle_show_hidden,
              [(wx.ACCEL_CTRL, ord('A'))],
              checkable=True, update_function=control.file_list.on_update_hidden_menu_item)
        )
        favorites_menu = (
         make(14001, _('Add to &favorites'), _('Add the current directory or compressed file to the favorites'),
              control.add_favorite,
              [(wx.ACCEL_CTRL, ord('D'))]),
         make(14002, _('R&emove from favorites'), _('Remove the current directory or compressed file from the favorites'),
              control.remove_favorite,
              [(wx.ACCEL_CTRL, ord('R'))]),
        )
        help_menu = (
          make(15001, _('&Help (online)...'), _('Open the online help'),
               control.open_help,
               [(wx.ACCEL_NORMAL, wx.WXK_F1)]),
          make(15002, _('&Feedback / Support (online)...'), _('Open the feedback / support online form'),
               control.open_feedback,
               []),
          make(wx.ID_ABOUT, _('&About...'), _('Show information about the application'),
               control.open_about_dialog,
               [])
        )
        hidden_menu = (
          make(16001, _('Small move up'), _('Small move up'),
               partial(control.canvas.move_image, canvas.MOVE_UP, canvas.MOVE_SMALL),
               [(wx.ACCEL_NORMAL, wx.WXK_UP)]),
          make(16002, _('Small move down'), _('Small move down'),
               partial(control.canvas.move_image, canvas.MOVE_DOWN, canvas.MOVE_SMALL),
               [(wx.ACCEL_NORMAL, wx.WXK_DOWN)]),
          make(16003, _('Small move left'), _('Small move left'),
               partial(control.canvas.move_image, canvas.MOVE_LEFT, canvas.MOVE_SMALL),
               [(wx.ACCEL_NORMAL, wx.WXK_LEFT)]),
          make(16004, _('Small move right'), _('Small move right'),
               partial(control.canvas.move_image, canvas.MOVE_RIGHT, canvas.MOVE_SMALL),
               [(wx.ACCEL_NORMAL, wx.WXK_RIGHT)]),
          make(16005, _('Large move up'), _('Large move up'),
               partial(control.canvas.move_image, canvas.MOVE_UP, canvas.MOVE_LARGE),
               [(wx.ACCEL_NORMAL, wx.WXK_PAGEUP)]),
          make(16006, _('Large move down'), _('Large move down'),
               partial(control.canvas.move_image, canvas.MOVE_DOWN, canvas.MOVE_LARGE),
               [(wx.ACCEL_NORMAL, wx.WXK_PAGEDOWN)]),
          make(16007, _('Large move left'), _('Large move left'),
               partial(control.canvas.move_image, canvas.MOVE_LEFT, canvas.MOVE_LARGE),
               []),
          make(16008, _('Large move right'), _('Large move right'),
               partial(control.canvas.move_image, canvas.MOVE_RIGHT, canvas.MOVE_LARGE),
               []),
        )
        fit_menu = (
          make(17001, _('None'), _('None'),
               partial(control.canvas.set_zoom_by_fit_type, Settings.FIT_NONE, save=True),
               []),
          make(17002, _('Width'), _('Width'),
               partial(control.canvas.set_zoom_by_fit_type, Settings.FIT_WIDTH, save=True),
               []),
          make(17003, _('Height'), _('Height'),
               partial(control.canvas.set_zoom_by_fit_type, Settings.FIT_HEIGHT, save=True),
               []),
          make(17004, _('Window'), _('Window'),
               partial(control.canvas.set_zoom_by_fit_type, Settings.FIT_BOTH, save=True),
               []),
          make(17005, _('Width if larger'), _('Width if larger'),
               partial(control.canvas.set_zoom_by_fit_type, Settings.FIT_WIDTH_OVERSIZE, save=True),
               []),
          make(17006, _('Height if larger'), _('Height if larger'),
               partial(control.canvas.set_zoom_by_fit_type, Settings.FIT_HEIGHT_OVERSIZE, save=True),
               []),
          make(17007, _('Window if larger'), _('Window if larger'),
               partial(control.canvas.set_zoom_by_fit_type, Settings.FIT_BOTH_OVERSIZE, save=True),
               []),
          #TODO: (2,2) Add: ask for the custom width?
          make(17008, _('Custom width'), _('Custom width'),
               partial(control.canvas.set_zoom_by_fit_type, Settings.FIT_CUSTOM_WIDTH, save=True),
               []),
        )
        #misc_menu = (
        #  make(18002, 'MF', 'MF',
        #       control.file_list.open_mf,
        #       []),
        #)
        main_menu = (
         make_category(0, _('&File'), file_menu),
         make_category(1, _('F&older'), folder_menu),
         make_category(2, _('&View'), view_menu),
         make_category(3, _('F&avorites'), favorites_menu),
         make_category(4, _('&Help'), help_menu),
         make_category(5, _('Move'), hidden_menu),
         make_category(6, _('Fit'), fit_menu),
         #make_category(7, _('Misc'), misc_menu),
        )
        return main_menu, commands
    
    @staticmethod
    def _get_toolbar_commands(commands):
        cmd_dict = dict((cmd.ide, cmd) for cmd in commands)
        #TODO: (2,2) Refactor: use constants
        cmd_ids = (12008, 14001, 14002, 12004, 13011)
        return tuple(cmd_dict[id] for id in cmd_ids)
    
    @staticmethod
    def _load_shortcuts(settings, commands):
        if settings.has_section(SHORTCUTS_KEY):
            cmd_dic = dict((cmd.ide, cmd) for cmd in commands)
            items = settings.items(SHORTCUTS_KEY)
            for cmd_id_str, shcut_lst_str in items:
                cmd_id = int(cmd_id_str)
                for shcut_str in shcut_lst_str.split():
                    shcut_lst = shcut_str.split(',')
                    key_code = int(shcut_lst[0])
                    flags = int(shcut_lst[1])
                    shcut = Shortcut(flags, key_code)
                    #TODO *(4,1): catch KeyErrors
                    if cmd_id in cmd_dic:
                        cmd_dic[cmd_id].shortcuts.append(shcut)
        else:
            MenuController._load_default_shortcuts(commands)
            
    @staticmethod
    def _save_shortcuts(settings, commands):
        settings.remove_section(SHORTCUTS_KEY)
        settings.add_section(SHORTCUTS_KEY)
        for cmd in commands:
            cmd_id_str = str(cmd.ide)
            shcut_lst_str = ' '.join('%d,%d' % (shcut.key_code, shcut.flags)
                                     for shcut in cmd.shortcuts)
            settings.set(SHORTCUTS_KEY, cmd_id_str, shcut_lst_str)
    
    @staticmethod
    def _load_default_shortcuts(commands):
        for cmd in commands:
            cmd.load_default_shortcut()
    
    @staticmethod
    def _get_accelerator_table(commands):
        lst = [(shcut.flags, shcut.key_code, cmd.ide) for cmd in commands
               for shcut in cmd.shortcuts] 
        return wx.AcceleratorTable(lst)