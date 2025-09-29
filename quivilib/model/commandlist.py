from enum import IntEnum, IntFlag, Flag, auto
from functools import partial
import wx

from quivilib.i18n import _
from quivilib.model.shortcut import Shortcut

class MovementType(Flag):
    MOVE = auto()
    MOVE_HORI = auto()
    MOVE_NEG = auto()
    
    MOVETYPE_SMALL = auto()
    MOVETYPE_LARGE = auto()
    MOVETYPE_FULL = auto()
    
    #Composite directions
    MOVE_LEFT = MOVE | MOVE_HORI
    MOVE_RIGHT = MOVE | MOVE_HORI | MOVE_NEG
    MOVE_UP = MOVE
    MOVE_DOWN = MOVE | MOVE_NEG

class FitSettings:
    #TODO: Proper enum.
    (FIT_NONE,
     FIT_WIDTH_OVERSIZE,
     FIT_HEIGHT_OVERSIZE,
     FIT_BOTH_OVERSIZE,
     FIT_CUSTOM_WIDTH,
     FIT_SCREEN_CROP_EXCESS,
     FIT_SCREEN_SHOW_ALL,
     FIT_SCREEN_NONE,
     FIT_TILED,
     FIT_WIDTH,
     FIT_HEIGHT,
     FIT_BOTH) = list(range(12))

class CommandFlags(IntFlag):
    NONE = 0
    KB = auto()          #Command can be assigned to a keyboard shortcut
    MOUSE = auto()       #Command can be assigned to a mouse button
    NOMENU = auto()      #Command does not appear in the application menu
    CHECKABLE = auto()   #Menu option can be shown as checked (requires an update function)
    DISABLEABLE = auto() #Menu option can be disabled (requires an update function)
    
    KBM = KB|MOUSE
    MASK = KB|MOUSE|NOMENU #Mask to ensure that at least one of these is set.
    
    #Using either CHECKABLE or DISABLEABLE requires that an update function is provided
    NEED_UPDATE = CHECKABLE | DISABLEABLE
#

class CommandName(IntEnum):
    """ Unique identifiers for all menu commands.
    """
    #file_menu
    SET_WALLPAPER = 11001
    COPY = 11002
    COPY_PATH = 11005
    DELETE = 11004
    MOVE = 11006
    OPTIONS = 11003
    QUIT = wx.ID_EXIT

    #folder_menu
    SELECT_NEXT = 12001
    SELECT_PREVIOUS = 12002
    OPEN_SELECTED_DIRECTORY = 12003
    OPEN_PARENT = 12004
    OPEN_NEXT  = 12005
    OPEN_PREVIOUS  = 12006
    REFRESH = 12007
    OPEN_DIRECTORY = 12008

    #view_menu
    ZOOM_IN = 13001
    ZOOM_OUT = 13002
    ZOOM_FULL = 13003
    FIT_WIDTH = 13004
    FIT_HEIGHT = 13005
    SHOW_SPREAD = 13040
    ROTATE_CLOCKWISE = 13008
    ROTATE_COUNTER_CLOCKWISE = 13009
    FULL_SCREEN = 13006
    SHOW_FILE_LIST = 13007
    SHOW_THUMBNAILS = 13011
    SHOW_HIDDEN_FILES = 13010

    #favorites_menu
    ADD_FAVORITES = 14001
    ADD_PLACEHOLDER = 14003
    REMOVE_FAVORITES = 14002
    REMOVE_PLACEHOLDER = 14004

    #favorites_hidden_menu
    OPEN_LAST_PLACEHOLDER = 14005
    #This doesn't belong here but I'm thinking this "menu group" crap needs to go.
    OPEN_CONTEXT_MENU = 18001

    #help_menu
    HELP = 15001
    FEEDBACK = 15002
    ABOUT = wx.ID_ABOUT

    #hidden_menu
    MOVE_SMALL_UP = 16001
    MOVE_SMALL_DOWN = 16002
    MOVE_SMALL_LEFT = 16003
    MOVE_SMALL_RIGHT = 16004
    MOVE_LARGE_UP = 16005
    MOVE_LARGE_DOWN = 16006
    MOVE_LARGE_LEFT = 16007
    MOVE_LARGE_RIGHT = 16008
    MOVE_FULL_UP = 16009
    MOVE_FULL_DOWN = 16010
    MOVE_FULL_LEFT = 16011
    MOVE_FULL_RIGHT = 16012
    DRAG_IMAGE = 16100

    #fit_menu
    ZOOM_NONE = 17001
    ZOOM_WIDTH = 17002
    ZOOM_HEIGHT = 17003
    ZOOM_WINDOW = 17004
    ZOOM_WIDTH_LARGER = 17005
    ZOOM_HEIGHT_LARGER = 17006
    ZOOM_WINDOW_LARGER = 17007
    ZOOM_CUSTOM_WIDTH = 17008
    
    #debug
    CACHE_INFO = 29900
#

class CommandDefinition():
    """ Definition of a menu CommandFlags. The unique id and name, but not any of the associated functions.
    The name and description are the translation key, but are not translated. This is to allow language switching.
    """
    def __init__(self, 
            uid: int, function,
            nameKey: str, descrKey: str, 
            shortcuts: list[tuple[wx.AcceleratorEntryFlags, wx.KeyCode|int]], 
            flags=CommandFlags.NONE, down_function=None, update_function=None):
        self.uid = uid
        self.nameKey = nameKey
        self.descrKey = descrKey
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
    def __repr__(self):
        return f"CommandDef: {self.nameKey}"
#

class CommandDefinitionList():
    """ The list of all Command Definitions. Actually stored as a dict.
    """

    def __init__(self, control):
        listItems = [
            #file_menu
            CommandDefinition(CommandName.SET_WALLPAPER            ,control.wallpaper.open_dialog, 'Set as &wallpaper...', 'Set the opened image as wallpaper', [(wx.ACCEL_NORMAL, wx.WXK_F3)], flags=CommandFlags.DISABLEABLE, update_function=control.on_update_image_available_menu_item),
            CommandDefinition(CommandName.COPY                     ,control.copy_to_clipboard, '&Copy', 'Copy the opened image to the clipboard',[(wx.ACCEL_CTRL, ord('C'))], flags=CommandFlags.DISABLEABLE, update_function=control.on_update_image_available_menu_item),
            CommandDefinition(CommandName.COPY_PATH                ,control.copy_path_to_clipboard, '&Copy path', 'Copy the path of the current container to the clipboard',[(wx.ACCEL_CTRL, ord('B'))], flags=CommandFlags.DISABLEABLE, update_function=control.on_update_image_available_menu_item),
            CommandDefinition(CommandName.DELETE                   ,control.delete, '&Delete', 'Delete the opened image',[(wx.ACCEL_CTRL, wx.WXK_DELETE)], flags=CommandFlags.DISABLEABLE, update_function=control.file_list.on_update_delete_menu_item),
            CommandDefinition(CommandName.MOVE                     ,control.open_move_dialog, '&Move...', 'Move the opened zip file to a new location',[(wx.ACCEL_CTRL, ord('N'))], flags=CommandFlags.DISABLEABLE, update_function=control.file_list.on_update_move_menu_item),
            CommandDefinition(CommandName.OPTIONS                  ,control.options.open_dialog, '&Options...', 'Open the options dialog',[(wx.ACCEL_NORMAL, wx.WXK_F4)]),
            CommandDefinition(CommandName.QUIT                     ,control.quit, '&Quit', 'Close the application',[], flags=CommandFlags.KB),
            
            #folder_menu
            CommandDefinition(CommandName.SELECT_NEXT              ,partial(control.file_list.select_next, 1), 'Select/Open &next', 'Select the next item; if it is an image, show it',[(wx.ACCEL_NORMAL, wx.WXK_END), (wx.ACCEL_NORMAL, wx.WXK_SPACE)]),
            CommandDefinition(CommandName.SELECT_PREVIOUS          ,partial(control.file_list.select_next, -1), 'Select/Open &previous', 'Select the previous item; if it is an image, show it',[(wx.ACCEL_NORMAL, wx.WXK_HOME)]),
            CommandDefinition(CommandName.OPEN_SELECTED_DIRECTORY  ,control.file_list.open_selected_container, 'Open selected &directory', 'If a directory or a compressed file is selected, open it',[(wx.ACCEL_NORMAL, wx.WXK_INSERT)]),
            CommandDefinition(CommandName.OPEN_PARENT              ,control.file_list.open_parent, 'Open p&arent', 'Open the parent directory or compressed file',[(wx.ACCEL_NORMAL, wx.WXK_DELETE)]),
            CommandDefinition(CommandName.OPEN_NEXT                ,partial(control.file_list.open_sibling, 1), 'Open ne&xt sibling', 'Open the next directory or compressed file inside the parent',[(wx.ACCEL_CTRL, wx.WXK_END)]),
            CommandDefinition(CommandName.OPEN_PREVIOUS            ,partial(control.file_list.open_sibling, -1), 'Open previou&s sibling', 'Open the previous directory or compressed file inside the parent',[(wx.ACCEL_CTRL, wx.WXK_HOME)]),
            CommandDefinition(CommandName.REFRESH                  ,control.file_list.refresh, '&Refresh', 'Refresh the current directory or compressed file; reload the image shown if any',[(wx.ACCEL_NORMAL, wx.WXK_F5)]),
            CommandDefinition(CommandName.OPEN_DIRECTORY           ,control.file_list.open_directory, 'Open direc&tory...', 'Browse for a directory to open',[(wx.ACCEL_CTRL, ord('O'))]),

            #view_menu
            CommandDefinition(CommandName.ZOOM_IN                  ,control.canvas.zoom_in, 'Zoom &in', 'Zoom in',[(wx.ACCEL_NORMAL, wx.WXK_NUMPAD_ADD)], flags=CommandFlags.DISABLEABLE, update_function=control.on_update_image_available_menu_item),
            CommandDefinition(CommandName.ZOOM_OUT                 ,control.canvas.zoom_out, 'Zoom &out', 'Zoom out',[(wx.ACCEL_NORMAL, wx.WXK_NUMPAD_SUBTRACT)], flags=CommandFlags.DISABLEABLE, update_function=control.on_update_image_available_menu_item),
            CommandDefinition(CommandName.ZOOM_FULL                ,control.canvas.zoom_reset, '&Zoom 100%', 'Show the image in its real size',[(wx.ACCEL_NORMAL, wx.WXK_NUMPAD_MULTIPLY)], flags=CommandFlags.DISABLEABLE, update_function=control.on_update_image_available_menu_item),
            CommandDefinition(CommandName.FIT_WIDTH                ,control.canvas.zoom_fit_width, 'Fit &width', 'Zooms the image in order to make its width fit the window',[(wx.ACCEL_CTRL, ord('W'))], flags=CommandFlags.DISABLEABLE, update_function=control.on_update_image_available_menu_item),
            CommandDefinition(CommandName.FIT_HEIGHT               ,control.canvas.zoom_fit_height, 'Fit &height', 'Zooms the image in order to make its height fit the window',[(wx.ACCEL_CTRL, ord('H'))], flags=CommandFlags.DISABLEABLE, update_function=control.on_update_image_available_menu_item),
            CommandDefinition(CommandName.SHOW_SPREAD              ,control.toggle_spread, 'Show &spread', 'Attempt to show combined pages at regular zoom',[(wx.ACCEL_CTRL, ord('E'))], flags=CommandFlags.CHECKABLE|CommandFlags.DISABLEABLE, update_function=control.on_update_spread_toggle_menu_item),
            CommandDefinition(CommandName.ROTATE_CLOCKWISE         ,partial(control.canvas.rotate_image, 1), 'Rotate &clockwise', 'Rotate the image clockwise',[(wx.ACCEL_CTRL, ord('L'))], flags=CommandFlags.DISABLEABLE, update_function=control.on_update_image_available_menu_item),
            CommandDefinition(CommandName.ROTATE_COUNTER_CLOCKWISE ,partial(control.canvas.rotate_image, 0), 'Rotate coun&ter clockwise', 'Rotate the image counter clockwise',[(wx.ACCEL_CTRL, ord('K'))], flags=CommandFlags.DISABLEABLE, update_function=control.on_update_image_available_menu_item),
            CommandDefinition(CommandName.FULL_SCREEN              ,control.toggle_fullscreen, '&Full screen', 'Go to/leave full screen mode',[(wx.ACCEL_ALT, wx.WXK_RETURN)], flags=CommandFlags.CHECKABLE|CommandFlags.DISABLEABLE, update_function=control.on_update_fullscreen_menu_item),
            CommandDefinition(CommandName.SHOW_FILE_LIST           ,control.toggle_file_list, 'File &list', 'Show/hide the file list',[(wx.ACCEL_NORMAL, wx.WXK_TAB)], flags=CommandFlags.CHECKABLE|CommandFlags.DISABLEABLE, update_function=control.on_update_file_list_menu_item),
            CommandDefinition(CommandName.SHOW_THUMBNAILS          ,control.toggle_thumbnails, 'Thumb&nails', 'Show/hide the thumbnails',[(wx.ACCEL_NORMAL, wx.WXK_F6)], flags=CommandFlags.CHECKABLE|CommandFlags.DISABLEABLE, update_function=control.on_update_thumbnail_menu_item),
            CommandDefinition(CommandName.SHOW_HIDDEN_FILES        ,control.file_list.toggle_show_hidden, 'Hi&dden files', 'Show/hide hidden files in the file list',[(wx.ACCEL_CTRL, ord('A'))], flags=CommandFlags.CHECKABLE|CommandFlags.DISABLEABLE, update_function=control.file_list.on_update_hidden_menu_item),
            
            #favorites_menu
            CommandDefinition(CommandName.ADD_FAVORITES            ,control.add_favorite, 'Add to &favorites', 'Add the current directory or compressed file to the favorites', [(wx.ACCEL_CTRL, ord('D'))]),
            CommandDefinition(CommandName.ADD_PLACEHOLDER          ,control.add_placeholder, 'Add &placeholder', 'Add the current directory or compressed file to the favorites on the current image',[(wx.ACCEL_CTRL, ord('F'))]),
            CommandDefinition(CommandName.REMOVE_FAVORITES         ,control.remove_favorite, 'R&emove from favorites', 'Remove the current directory or compressed file from the favorites',[(wx.ACCEL_CTRL, ord('R'))]),
            CommandDefinition(CommandName.REMOVE_PLACEHOLDER       ,control.remove_placeholder, 'Remove p&laceholder', 'Remove the saved page for the current directory or compressed file from the favorites',[(wx.ACCEL_CTRL, ord('V'))]),
            
            #favorites_hidden_menu
            CommandDefinition(CommandName.OPEN_LAST_PLACEHOLDER    , control.open_latest_placeholder, 'Open last placeholder', 'Open the most recently created placeholder',[(wx.ACCEL_CTRL, ord('L'))]),
            CommandDefinition(CommandName.OPEN_CONTEXT_MENU        , control.open_context_menu, 'Open context menu', 'Open the context menu', [], flags=CommandFlags.MOUSE),
            
            #help_menu
            CommandDefinition(CommandName.HELP                     ,control.open_help, '&Help (online)...', 'Open the online help',[(wx.ACCEL_NORMAL, wx.WXK_F1)], flags=CommandFlags.KB),
            CommandDefinition(CommandName.FEEDBACK                 ,control.open_feedback, '&Feedback / Support (online)...', 'Open the feedback / support online form',[], flags=CommandFlags.KB),
            CommandDefinition(CommandName.ABOUT                    ,control.open_about_dialog, '&About...', 'Show information about the application',[], flags=CommandFlags.KB),
            
            #hidden_menu
            CommandDefinition(CommandName.MOVE_SMALL_UP            ,partial(control.canvas.move_image, MovementType.MOVE_UP, MovementType.MOVETYPE_SMALL), 'Small move up', 'Small move up',[(wx.ACCEL_NORMAL, wx.WXK_UP)], flags=CommandFlags.KB),
            CommandDefinition(CommandName.MOVE_SMALL_DOWN          ,partial(control.canvas.move_image, MovementType.MOVE_DOWN, MovementType.MOVETYPE_SMALL), 'Small move down', 'Small move down',[(wx.ACCEL_NORMAL, wx.WXK_DOWN)], flags=CommandFlags.KB),
            CommandDefinition(CommandName.MOVE_SMALL_LEFT          ,partial(control.canvas.move_image, MovementType.MOVE_LEFT, MovementType.MOVETYPE_SMALL), 'Small move left', 'Small move left',[(wx.ACCEL_NORMAL, wx.WXK_LEFT)], flags=CommandFlags.KB),
            CommandDefinition(CommandName.MOVE_SMALL_RIGHT         ,partial(control.canvas.move_image, MovementType.MOVE_RIGHT, MovementType.MOVETYPE_SMALL), 'Small move right', 'Small move right',[(wx.ACCEL_NORMAL, wx.WXK_RIGHT)], flags=CommandFlags.KB),
            CommandDefinition(CommandName.MOVE_LARGE_UP            ,partial(control.canvas.move_image, MovementType.MOVE_UP, MovementType.MOVETYPE_LARGE), 'Large move up', 'Large move up',[(wx.ACCEL_NORMAL, wx.WXK_PAGEUP)], flags=CommandFlags.KB),
            CommandDefinition(CommandName.MOVE_LARGE_DOWN          ,partial(control.canvas.move_image, MovementType.MOVE_DOWN, MovementType.MOVETYPE_LARGE) , 'Large move down', 'Large move down',[(wx.ACCEL_NORMAL, wx.WXK_PAGEDOWN)], flags=CommandFlags.KB),
            CommandDefinition(CommandName.MOVE_LARGE_LEFT          ,partial(control.canvas.move_image, MovementType.MOVE_LEFT, MovementType.MOVETYPE_LARGE) , 'Large move left', 'Large move left', [], flags=CommandFlags.KB),
            CommandDefinition(CommandName.MOVE_LARGE_RIGHT         ,partial(control.canvas.move_image, MovementType.MOVE_RIGHT, MovementType.MOVETYPE_LARGE), 'Large move right', 'Large move right',[], flags=CommandFlags.KB),
            CommandDefinition(CommandName.MOVE_FULL_UP             ,partial(control.canvas.move_image, MovementType.MOVE_UP, MovementType.MOVETYPE_FULL)    , 'Full move up', 'Full move up',[], flags=CommandFlags.KB),
            CommandDefinition(CommandName.MOVE_FULL_DOWN           ,partial(control.canvas.move_image, MovementType.MOVE_DOWN, MovementType.MOVETYPE_FULL)  , 'Full move down', 'Full move down',[], flags=CommandFlags.KB),
            CommandDefinition(CommandName.MOVE_FULL_LEFT           ,partial(control.canvas.move_image, MovementType.MOVE_LEFT, MovementType.MOVETYPE_FULL)  , 'Full move left', 'Full move left',[], flags=CommandFlags.KB),
            CommandDefinition(CommandName.MOVE_FULL_RIGHT          ,partial(control.canvas.move_image, MovementType.MOVE_RIGHT, MovementType.MOVETYPE_FULL) , 'Full move right', 'Full move right',[], flags=CommandFlags.KB),
            CommandDefinition(CommandName.DRAG_IMAGE               ,control.canvas.image_drag_end, 'Drag image', 'Drag image',[], flags=CommandFlags.MOUSE, down_function=control.canvas.image_drag_start),
            
            #fit_menu
            CommandDefinition(CommandName.ZOOM_NONE                ,partial(control.canvas.set_zoom_by_fit_type, FitSettings.FIT_NONE, save=True)           , 'None', 'None',[]),
            CommandDefinition(CommandName.ZOOM_WIDTH               ,partial(control.canvas.set_zoom_by_fit_type, FitSettings.FIT_WIDTH, save=True)          , 'Width', 'Width',[]),
            CommandDefinition(CommandName.ZOOM_HEIGHT              ,partial(control.canvas.set_zoom_by_fit_type, FitSettings.FIT_HEIGHT, save=True)         , 'Height', 'Height',[]),
            CommandDefinition(CommandName.ZOOM_WINDOW              ,partial(control.canvas.set_zoom_by_fit_type, FitSettings.FIT_BOTH , save=True)          , 'Window', 'Window',[]),
            CommandDefinition(CommandName.ZOOM_WIDTH_LARGER        ,partial(control.canvas.set_zoom_by_fit_type, FitSettings.FIT_WIDTH_OVERSIZE, save=True) , 'Width if larger', 'Width if larger',[]),
            CommandDefinition(CommandName.ZOOM_HEIGHT_LARGER       ,partial(control.canvas.set_zoom_by_fit_type, FitSettings.FIT_HEIGHT_OVERSIZE, save=True), 'Height if larger', 'Height if larger',[]),
            CommandDefinition(CommandName.ZOOM_WINDOW_LARGER       ,partial(control.canvas.set_zoom_by_fit_type, FitSettings.FIT_BOTH_OVERSIZE, save=True)  , 'Window if larger', 'Window if larger',[]),
            CommandDefinition(CommandName.ZOOM_CUSTOM_WIDTH        ,partial(control.canvas.set_zoom_by_fit_type, FitSettings.FIT_CUSTOM_WIDTH, save=True), 'Custom width', 'Custom width',[]),

            #debug menu
            CommandDefinition(CommandName.CACHE_INFO               ,control.debugController.open_debug_cache_dialog, 'Cache', 'Show Cache information',[]),
        ]
        self.commands = {x.uid: x for x in listItems}
#