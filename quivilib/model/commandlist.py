from functools import partial
from typing import Sequence
import wx

from quivilib.i18n import _
from quivilib.model.shortcut import Shortcut
from quivilib.model.commandenum import *


class CommandDefinition():
    """ Static Definition of a menu item. Includes everything but the applied translations.
    The name and description are the translation key, but are not translated. This is to allow language switching.
    """
    def __init__(self, 
            uid: CommandName, catNameKey: str, function,
            nameKey: str, descrKey: str, 
            shortcuts: list[tuple[wx.AcceleratorEntryFlags, wx.KeyCode|int]], 
            flags: CommandFlags = CommandFlags.NONE, down_function=None, update_function=None):
        """ Creates a new command definition.
        
        @param uid: Unique identifier, a declared enum value
        @param catNameKey: Name of the group/menubar this belongs too. Untranslated key.
        @param function: Callable function to be executed when "normally" invoking this command.
        @param nameKey: Name of this command/menu item. Untranslated key.
        @param descrKey: Longer text description of this command/menu item. Untranslated key.
        @param shortcuts: (List of) key combinations that will execute this command
        @param flags: Flags enum, used to control how this menu items is used/displayed.
        @param down_function: Callable function to be executed when holding down the mouse key
        @param update_function: Callable function, used to enable/disable or check/uncheck this item.
        """
        self.uid = uid
        self.nameKey = nameKey
        self.descrKey = descrKey
        self.categoryKey = catNameKey
        self.shortcuts = [Shortcut(*x) for x in shortcuts]
        self.function = function
        self.down_function = down_function
        self.update_function = update_function
        if ((flags & CommandFlags.MASK) == 0):
            flags |= CommandFlags.KBM
        self.flags = flags
        
        #Some consistency checks
        need_update = (flags & CommandFlags.NEED_UPDATE) != 0
        if (need_update and update_function is None):
            raise Exception(f"Menu item {self.clean_name} requires an update function but doesn't have one")
        if (not need_update and update_function is not None):
            raise Exception(f"Menu item {self.clean_name} was given an update function but can't use one")
    #
    @staticmethod
    def clean_str(s):
        return s.replace('&', '').replace('...', '')
    @property
    def clean_name(self):
        return self.clean_str(self.nameKey)
    def __repr__(self):
        return f"CommandDef: {self.nameKey}"
#

class CommandDefinitionList():
    """ The list of all Command Definitions. Actually stored as a dict.
    """

    #TODO: Break these up into multiple lines. Check the cmddef ctor. Try to follow that.
    def __init__(self, control):
        def list_items():
            cat_name = '&File'
            yield CommandDefinition(CommandName.SET_WALLPAPER            ,cat_name,control.wallpaper.open_dialog, 'Set as &wallpaper...', 'Set the opened image as wallpaper', [(wx.ACCEL_NORMAL, wx.WXK_F3)], flags=CommandFlags.DISABLEABLE, update_function=control.on_update_image_available_menu_item)
            yield CommandDefinition(CommandName.COPY                     ,cat_name,control.copy_to_clipboard, '&Copy', 'Copy the opened image to the clipboard',[(wx.ACCEL_CTRL, ord('C'))], flags=CommandFlags.DISABLEABLE, update_function=control.on_update_image_available_menu_item)
            yield CommandDefinition(CommandName.COPY_PATH                ,cat_name,control.copy_path_to_clipboard, '&Copy path', 'Copy the path of the current container to the clipboard',[(wx.ACCEL_CTRL, ord('B'))], flags=CommandFlags.DISABLEABLE, update_function=control.on_update_image_available_menu_item)
            yield CommandDefinition(CommandName.DELETE                   ,cat_name,control.delete, '&Delete', 'Delete the opened image',[(wx.ACCEL_CTRL, wx.WXK_DELETE)], flags=CommandFlags.DISABLEABLE, update_function=control.file_list.on_update_delete_menu_item)
            yield CommandDefinition(CommandName.MOVE                     ,cat_name,control.open_move_dialog, '&Move...', 'Move the opened zip file to a new location',[(wx.ACCEL_CTRL, ord('N'))], flags=CommandFlags.DISABLEABLE, update_function=control.file_list.on_update_move_menu_item)
            yield CommandDefinition(CommandName.OPTIONS                  ,cat_name,control.options.open_dialog, '&Options...', 'Open the options dialog',[(wx.ACCEL_NORMAL, wx.WXK_F4)])
            yield CommandDefinition(CommandName.QUIT                     ,cat_name,control.quit, '&Quit', 'Close the application',[], flags=CommandFlags.KB)
            
            cat_name = 'F&older'
            yield CommandDefinition(CommandName.SELECT_NEXT              ,cat_name,partial(control.file_list.select_next, 1), 'Select/Open &next', 'Select the next item; if it is an image, show it',[(wx.ACCEL_NORMAL, wx.WXK_END), (wx.ACCEL_NORMAL, wx.WXK_SPACE)])
            yield CommandDefinition(CommandName.SELECT_PREVIOUS          ,cat_name,partial(control.file_list.select_next, -1), 'Select/Open &previous', 'Select the previous item; if it is an image, show it',[(wx.ACCEL_NORMAL, wx.WXK_HOME)])
            yield CommandDefinition(CommandName.OPEN_SELECTED_DIRECTORY  ,cat_name,control.file_list.open_selected_container, 'Open selected &directory', 'If a directory or a compressed file is selected, open it',[(wx.ACCEL_NORMAL, wx.WXK_INSERT)])
            yield CommandDefinition(CommandName.OPEN_PARENT              ,cat_name,control.file_list.open_parent, 'Open p&arent', 'Open the parent directory or compressed file',[(wx.ACCEL_NORMAL, wx.WXK_DELETE)])
            yield CommandDefinition(CommandName.OPEN_NEXT                ,cat_name,partial(control.file_list.open_sibling, 1), 'Open ne&xt sibling', 'Open the next directory or compressed file inside the parent',[(wx.ACCEL_CTRL, wx.WXK_END)])
            yield CommandDefinition(CommandName.OPEN_PREVIOUS            ,cat_name,partial(control.file_list.open_sibling, -1), 'Open previou&s sibling', 'Open the previous directory or compressed file inside the parent',[(wx.ACCEL_CTRL, wx.WXK_HOME)])
            yield CommandDefinition(CommandName.REFRESH                  ,cat_name,control.file_list.refresh, '&Refresh', 'Refresh the current directory or compressed file; reload the image shown if any',[(wx.ACCEL_NORMAL, wx.WXK_F5)])
            yield CommandDefinition(CommandName.OPEN_DIRECTORY           ,cat_name,control.file_list.open_directory, 'Open direc&tory...', 'Browse for a directory to open',[(wx.ACCEL_CTRL, ord('O'))])

            cat_name = '&View'
            yield CommandDefinition(CommandName.ZOOM_IN                  ,cat_name,control.canvas.zoom_in, 'Zoom &in', 'Zoom in',[(wx.ACCEL_NORMAL, wx.WXK_NUMPAD_ADD)], flags=CommandFlags.DISABLEABLE, update_function=control.on_update_image_available_menu_item)
            yield CommandDefinition(CommandName.ZOOM_OUT                 ,cat_name,control.canvas.zoom_out, 'Zoom &out', 'Zoom out',[(wx.ACCEL_NORMAL, wx.WXK_NUMPAD_SUBTRACT)], flags=CommandFlags.DISABLEABLE, update_function=control.on_update_image_available_menu_item)
            yield CommandDefinition(CommandName.ZOOM_FULL                ,cat_name,control.canvas.zoom_reset, '&Zoom 100%', 'Show the image in its real size',[(wx.ACCEL_NORMAL, wx.WXK_NUMPAD_MULTIPLY)], flags=CommandFlags.DISABLEABLE, update_function=control.on_update_image_available_menu_item)
            yield CommandDefinition(CommandName.FIT_WIDTH                ,cat_name,control.canvas.zoom_fit_width, 'Fit &width', 'Zooms the image in order to make its width fit the window',[(wx.ACCEL_CTRL, ord('W'))], flags=CommandFlags.DISABLEABLE, update_function=control.on_update_image_available_menu_item)
            yield CommandDefinition(CommandName.FIT_HEIGHT               ,cat_name,control.canvas.zoom_fit_height, 'Fit &height', 'Zooms the image in order to make its height fit the window',[(wx.ACCEL_CTRL, ord('H'))], flags=CommandFlags.DISABLEABLE, update_function=control.on_update_image_available_menu_item)
            yield CommandDefinition(CommandName.SHOW_SPREAD              ,cat_name,control.toggle_spread, 'Show &spread', 'Attempt to show combined pages at regular zoom',[(wx.ACCEL_CTRL, ord('E'))], flags=CommandFlags.CHECKABLE|CommandFlags.DISABLEABLE, update_function=control.on_update_spread_toggle_menu_item)
            yield CommandDefinition(CommandName.ROTATE_CLOCKWISE         ,cat_name,partial(control.canvas.rotate_image, 1), 'Rotate &clockwise', 'Rotate the image clockwise',[(wx.ACCEL_CTRL, ord('L'))], flags=CommandFlags.DISABLEABLE, update_function=control.on_update_image_available_menu_item)
            yield CommandDefinition(CommandName.ROTATE_COUNTER_CLOCKWISE ,cat_name,partial(control.canvas.rotate_image, 0), 'Rotate coun&ter clockwise', 'Rotate the image counter clockwise',[(wx.ACCEL_CTRL, ord('K'))], flags=CommandFlags.DISABLEABLE, update_function=control.on_update_image_available_menu_item)
            yield CommandDefinition(CommandName.FULL_SCREEN              ,cat_name,control.toggle_fullscreen, '&Full screen', 'Go to/leave full screen mode',[(wx.ACCEL_ALT, wx.WXK_RETURN)], flags=CommandFlags.CHECKABLE|CommandFlags.DISABLEABLE, update_function=control.on_update_fullscreen_menu_item)
            yield CommandDefinition(CommandName.SHOW_FILE_LIST           ,cat_name,control.toggle_file_list, 'File &list', 'Show/hide the file list',[(wx.ACCEL_NORMAL, wx.WXK_TAB)], flags=CommandFlags.CHECKABLE|CommandFlags.DISABLEABLE, update_function=control.on_update_file_list_menu_item)
            yield CommandDefinition(CommandName.SHOW_THUMBNAILS          ,cat_name,control.toggle_thumbnails, 'Thumb&nails', 'Show/hide the thumbnails',[(wx.ACCEL_NORMAL, wx.WXK_F6)], flags=CommandFlags.CHECKABLE|CommandFlags.DISABLEABLE, update_function=control.on_update_thumbnail_menu_item)
            yield CommandDefinition(CommandName.SHOW_HIDDEN_FILES        ,cat_name,control.file_list.toggle_show_hidden, 'Hi&dden files', 'Show/hide hidden files in the file list',[(wx.ACCEL_CTRL, ord('A'))], flags=CommandFlags.CHECKABLE|CommandFlags.DISABLEABLE, update_function=control.file_list.on_update_hidden_menu_item)
            
            cat_name = 'F&avorites'
            yield CommandDefinition(CommandName.ADD_FAVORITES            ,cat_name,control.add_favorite, 'Add to &favorites', 'Add the current directory or compressed file to the favorites', [(wx.ACCEL_CTRL, ord('D'))])
            yield CommandDefinition(CommandName.ADD_PLACEHOLDER          ,cat_name,control.add_placeholder, 'Add &placeholder', 'Add the current directory or compressed file to the favorites on the current image',[(wx.ACCEL_CTRL, ord('F'))])
            yield CommandDefinition(CommandName.REMOVE_FAVORITES         ,cat_name,control.remove_favorite, 'R&emove from favorites', 'Remove the current directory or compressed file from the favorites',[(wx.ACCEL_CTRL, ord('R'))])
            yield CommandDefinition(CommandName.REMOVE_PLACEHOLDER       ,cat_name,control.remove_placeholder, 'Remove p&laceholder', 'Remove the saved page for the current directory or compressed file from the favorites',[(wx.ACCEL_CTRL, ord('V'))])
            
            cat_name = 'F&avorites'
            yield CommandDefinition(CommandName.OPEN_LAST_PLACEHOLDER    ,cat_name, control.open_latest_placeholder, 'Open last placeholder', 'Open the most recently created placeholder',[(wx.ACCEL_CTRL, ord('L'))])
            yield CommandDefinition(CommandName.OPEN_CONTEXT_MENU        ,cat_name, control.open_context_menu, 'Open context menu', 'Open the context menu', [], flags=CommandFlags.MOUSE)
            
            cat_name = '&Help'
            yield CommandDefinition(CommandName.HELP                     ,cat_name,control.open_help, '&Help (online)...', 'Open the online help',[(wx.ACCEL_NORMAL, wx.WXK_F1)], flags=CommandFlags.KB)
            yield CommandDefinition(CommandName.FEEDBACK                 ,cat_name,control.open_feedback, '&Feedback / Support (online)...', 'Open the feedback / support online form',[], flags=CommandFlags.KB)
            yield CommandDefinition(CommandName.ABOUT                    ,cat_name,control.open_about_dialog, '&About...', 'Show information about the application',[], flags=CommandFlags.KB)
            
            cat_name = 'Move'
            yield CommandDefinition(CommandName.MOVE_SMALL_UP            ,cat_name,partial(control.canvas.move_image, MovementType.MOVE_UP, MovementType.MOVETYPE_SMALL), 'Small move up', 'Small move up',[(wx.ACCEL_NORMAL, wx.WXK_UP)], flags=CommandFlags.KB)
            yield CommandDefinition(CommandName.MOVE_SMALL_DOWN          ,cat_name,partial(control.canvas.move_image, MovementType.MOVE_DOWN, MovementType.MOVETYPE_SMALL), 'Small move down', 'Small move down',[(wx.ACCEL_NORMAL, wx.WXK_DOWN)], flags=CommandFlags.KB)
            yield CommandDefinition(CommandName.MOVE_SMALL_LEFT          ,cat_name,partial(control.canvas.move_image, MovementType.MOVE_LEFT, MovementType.MOVETYPE_SMALL), 'Small move left', 'Small move left',[(wx.ACCEL_NORMAL, wx.WXK_LEFT)], flags=CommandFlags.KB)
            yield CommandDefinition(CommandName.MOVE_SMALL_RIGHT         ,cat_name,partial(control.canvas.move_image, MovementType.MOVE_RIGHT, MovementType.MOVETYPE_SMALL), 'Small move right', 'Small move right',[(wx.ACCEL_NORMAL, wx.WXK_RIGHT)], flags=CommandFlags.KB)
            yield CommandDefinition(CommandName.MOVE_LARGE_UP            ,cat_name,partial(control.canvas.move_image, MovementType.MOVE_UP, MovementType.MOVETYPE_LARGE), 'Large move up', 'Large move up',[(wx.ACCEL_NORMAL, wx.WXK_PAGEUP)], flags=CommandFlags.KB)
            yield CommandDefinition(CommandName.MOVE_LARGE_DOWN          ,cat_name,partial(control.canvas.move_image, MovementType.MOVE_DOWN, MovementType.MOVETYPE_LARGE) , 'Large move down', 'Large move down',[(wx.ACCEL_NORMAL, wx.WXK_PAGEDOWN)], flags=CommandFlags.KB)
            yield CommandDefinition(CommandName.MOVE_LARGE_LEFT          ,cat_name,partial(control.canvas.move_image, MovementType.MOVE_LEFT, MovementType.MOVETYPE_LARGE) , 'Large move left', 'Large move left', [], flags=CommandFlags.KB)
            yield CommandDefinition(CommandName.MOVE_LARGE_RIGHT         ,cat_name,partial(control.canvas.move_image, MovementType.MOVE_RIGHT, MovementType.MOVETYPE_LARGE), 'Large move right', 'Large move right',[], flags=CommandFlags.KB)
            yield CommandDefinition(CommandName.MOVE_FULL_UP             ,cat_name,partial(control.canvas.move_image, MovementType.MOVE_UP, MovementType.MOVETYPE_FULL)    , 'Full move up', 'Full move up',[], flags=CommandFlags.KB)
            yield CommandDefinition(CommandName.MOVE_FULL_DOWN           ,cat_name,partial(control.canvas.move_image, MovementType.MOVE_DOWN, MovementType.MOVETYPE_FULL)  , 'Full move down', 'Full move down',[], flags=CommandFlags.KB)
            yield CommandDefinition(CommandName.MOVE_FULL_LEFT           ,cat_name,partial(control.canvas.move_image, MovementType.MOVE_LEFT, MovementType.MOVETYPE_FULL)  , 'Full move left', 'Full move left',[], flags=CommandFlags.KB)
            yield CommandDefinition(CommandName.MOVE_FULL_RIGHT          ,cat_name,partial(control.canvas.move_image, MovementType.MOVE_RIGHT, MovementType.MOVETYPE_FULL) , 'Full move right', 'Full move right',[], flags=CommandFlags.KB)
            yield CommandDefinition(CommandName.DRAG_IMAGE               ,cat_name,control.canvas.image_drag_end, 'Drag image', 'Drag image',[], flags=CommandFlags.MOUSE, down_function=control.canvas.image_drag_start)
            
            cat_name = 'Fit'
            yield CommandDefinition(CommandName.ZOOM_NONE                ,cat_name,partial(control.canvas.set_zoom_by_fit_type, FitSettings.FIT_NONE, save=True)           , 'None', 'None',[])
            yield CommandDefinition(CommandName.ZOOM_WIDTH               ,cat_name,partial(control.canvas.set_zoom_by_fit_type, FitSettings.FIT_WIDTH, save=True)          , 'Width', 'Width',[])
            yield CommandDefinition(CommandName.ZOOM_HEIGHT              ,cat_name,partial(control.canvas.set_zoom_by_fit_type, FitSettings.FIT_HEIGHT, save=True)         , 'Height', 'Height',[])
            yield CommandDefinition(CommandName.ZOOM_WINDOW              ,cat_name,partial(control.canvas.set_zoom_by_fit_type, FitSettings.FIT_BOTH , save=True)          , 'Window', 'Window',[])
            yield CommandDefinition(CommandName.ZOOM_WIDTH_LARGER        ,cat_name,partial(control.canvas.set_zoom_by_fit_type, FitSettings.FIT_WIDTH_OVERSIZE, save=True) , 'Width if larger', 'Width if larger',[])
            yield CommandDefinition(CommandName.ZOOM_HEIGHT_LARGER       ,cat_name,partial(control.canvas.set_zoom_by_fit_type, FitSettings.FIT_HEIGHT_OVERSIZE, save=True), 'Height if larger', 'Height if larger',[])
            yield CommandDefinition(CommandName.ZOOM_WINDOW_LARGER       ,cat_name,partial(control.canvas.set_zoom_by_fit_type, FitSettings.FIT_BOTH_OVERSIZE, save=True)  , 'Window if larger', 'Window if larger',[])
            yield CommandDefinition(CommandName.ZOOM_CUSTOM_WIDTH        ,cat_name,partial(control.canvas.set_zoom_by_fit_type, FitSettings.FIT_CUSTOM_WIDTH, save=True), 'Custom width', 'Custom width',[])

            cat_name = 'Download'
            yield CommandDefinition(CommandName.DOWNLOAD_NEW             ,cat_name,control.view.on_download_update, '&Download', 'Go to the download site',[], flags=CommandFlags.NOMENU)

            cat_name = 'Debug'
            yield CommandDefinition(CommandName.CACHE_INFO               ,cat_name,control.debugController.open_debug_cache_dialog, 'Cache', 'Show Cache information',[], flags=CommandFlags.NOMENU)
            yield CommandDefinition(CommandName.CHECK_UPDATE             ,cat_name,control.check_updates, 'Check for Updates', 'Reset check-for-updates timestamp',[], flags=CommandFlags.NOMENU)
        #
        self.cmd_list = [x for x in list_items()]
        self.commands = {x.uid: x for x in self.cmd_list}
#

class MenuDefinition():
    def __init__(self, ide: MenuName, nameKey: str, commands: Sequence[None|MenuName|CommandName]):
        self.menu_id = ide
        self.nameKey = nameKey
        self.commands = commands

class MenuDefinitionList():
    """ Lists out the contents of every menu that can appear in the application.
    This is the name/description and the contents,
    contents are either None (separator), a CommandName, or a MenuName (i.e. a sub menu)
    """
    def __init__(self):
        #For text fields deliberately left blank
        empty = ''
        #Top-level
        file_menu = MenuDefinition(MenuName.File, '&File', (
            CommandName.SET_WALLPAPER,
            CommandName.COPY,
            CommandName.COPY_PATH,
            CommandName.DELETE,
            CommandName.MOVE,
            None,
            CommandName.OPTIONS,
            None,
            CommandName.QUIT
        ))
        folder_menu = MenuDefinition(MenuName.Folder, 'F&older', (
            CommandName.SELECT_NEXT,
            CommandName.SELECT_PREVIOUS,
            CommandName.OPEN_SELECTED_DIRECTORY,
            CommandName.OPEN_PARENT,
            CommandName.OPEN_NEXT,
            CommandName.OPEN_PREVIOUS,
            CommandName.REFRESH,
            CommandName.OPEN_DIRECTORY,
        ))
        view_menu = MenuDefinition(MenuName.View, '&View', (
            CommandName.ZOOM_IN,
            CommandName.ZOOM_OUT,
            #TODO: Add mouse-specific version that zooms in on mouse position. Also give it NOMENU.
            #When NOMENU is implemented, also remove the hidden menus.
            CommandName.ZOOM_FULL,
            CommandName.FIT_WIDTH,
            CommandName.FIT_HEIGHT,
            #TODO: All the messaging around this feature is awful but I don't know how to better word it.
            CommandName.SHOW_SPREAD,
            CommandName.ROTATE_CLOCKWISE,
            CommandName.ROTATE_COUNTER_CLOCKWISE,
            None,
            CommandName.FULL_SCREEN,
            CommandName.SHOW_FILE_LIST,
            CommandName.SHOW_THUMBNAILS,
            CommandName.SHOW_HIDDEN_FILES,
        ))
        favorites_menu = MenuDefinition(MenuName.Favorites, 'F&avorites', (
            CommandName.ADD_FAVORITES,
            CommandName.ADD_PLACEHOLDER,
            CommandName.REMOVE_FAVORITES,
            CommandName.REMOVE_PLACEHOLDER,
        ))
        help_menu = MenuDefinition(MenuName.Help, '&Help', (
            CommandName.HELP,
            CommandName.FEEDBACK,
            CommandName.ABOUT,
        ))
        download_menu = MenuDefinition(MenuName.Downloads, '&New version available!', (
            CommandName.DOWNLOAD_NEW,
        ))
        #Debug mode only
        debug_menu = MenuDefinition(MenuName.Debug, 'Debug', (
            CommandName.CACHE_INFO,
            CommandName.CHECK_UPDATE,
        ))
        #Sub menus
        zoom_sub = MenuDefinition(MenuName.ZoomSub, 'Zoom', (
            CommandName.ZOOM_IN,   
            CommandName.ZOOM_OUT,  
            CommandName.ZOOM_FULL, 
            CommandName.FIT_WIDTH,
            CommandName.FIT_HEIGHT,
        ))
        rotate_sub = MenuDefinition(MenuName.RotateSub, 'Rotate', (
            CommandName.ROTATE_CLOCKWISE,        
            CommandName.ROTATE_COUNTER_CLOCKWISE,
        ))
        fav_sub = MenuDefinition(MenuName.FavoritesSub, 'Favorites', (
            #Deliberately empty
        ))
        placeholder_sub = MenuDefinition(MenuName.PlaceholderSub, 'Placeholders', (
            #Deliberately empty
        ))
        # Context menus
        fit_menu = MenuDefinition(MenuName.FitCtx, empty, (
            CommandName.ZOOM_NONE,
            CommandName.ZOOM_WIDTH,
            CommandName.ZOOM_HEIGHT,
            CommandName.ZOOM_WINDOW,
            CommandName.ZOOM_WIDTH_LARGER,
            CommandName.ZOOM_HEIGHT_LARGER,
            CommandName.ZOOM_WINDOW_LARGER,
            # TODO: (2,2) Add: ask for the custom width?
            CommandName.ZOOM_CUSTOM_WIDTH,
        ))
        img_context = MenuDefinition(MenuName.ImgCtx, empty, (
            CommandName.OPEN_DIRECTORY,
            CommandName.SELECT_NEXT,
            CommandName.SELECT_PREVIOUS,
            CommandName.MOVE,
            None,
            MenuName.ZoomSub,
            MenuName.RotateSub,
            CommandName.SHOW_SPREAD,
            None,
            CommandName.FULL_SCREEN,
            CommandName.SHOW_FILE_LIST,
            None,
            # favorites, #MenuName.Favorites
            # None,
            CommandName.OPTIONS,
            CommandName.HELP,
            CommandName.ABOUT,
            None,
            CommandName.QUIT,
        ))

        self.menubar_menus = (file_menu, folder_menu, view_menu, favorites_menu, help_menu)
        if __debug__:
            self.menubar_menus = self.menubar_menus + (debug_menu,)
        self.menu_list = (
            file_menu, folder_menu, view_menu, favorites_menu, help_menu, download_menu,
            zoom_sub, rotate_sub, fav_sub, placeholder_sub,
            fit_menu, img_context,
            debug_menu,
        )
    #
