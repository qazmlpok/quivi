import wx

wxEVT_COMMAND_HOTKEY_UPDATED = wx.NewEventType()
EVT_HOTKEY = wx.PyEventBinder(wxEVT_COMMAND_HOTKEY_UPDATED, 1)

_dic = {}

def _setup():
    #There are synonymous with better names (Pagedown/up)
    ignore = {'WXK_PRIOR', 'WXK_NEXT', 'WXK_NUMPAD_NEXT', 'WXK_NUMPAD_PRIOR'}
    for name in wx.__dict__:
        if name.startswith('WXK_'):
            key_code = wx.__dict__[name]
            if name not in ignore:
                _dic[key_code] = str(name[4:].replace('_', ' ').title())

_setup()

def GetHotkeyName(key_code: int, modifiers: wx.KeyModifier) -> str:
    name = GetKeyName(key_code)
    mod_name = GetModifiersName(modifiers)
    if key_code in (wx.WXK_CONTROL, wx.WXK_SHIFT, wx.WXK_ALT, wx.WXK_COMMAND):
        return mod_name
    elif mod_name:
        return mod_name + '+' + name
    else:
        return name
    
def GetAcceleratorName(accelerator: wx.AcceleratorEntry|tuple[int, int]) -> str:
    if isinstance(accelerator, wx.AcceleratorEntry):
        key_code = accelerator.GetKeyCode()
        flags = accelerator.GetFlags()
    else:
        key_code = accelerator[1]
        flags = accelerator[0]
    return GetHotkeyName(key_code, ConvertFlagsToModifiers(flags))
    
def GetKeyName(key_code: int) -> str:
    #TODO: (1,2) Improve: call Windows GetKeyNameText?
    try:
        return _dic[key_code]
    except KeyError:
        try:
            return chr(key_code)
        except ValueError:
            return '[Unknown]'
        
def GetModifiersName(modifiers: wx.KeyModifier) -> str:
    lst = []
    if modifiers & wx.MOD_CMD and wx.MOD_CMD == wx.MOD_META:
        lst.append('Cmd')
    if modifiers & wx.MOD_CONTROL:
        lst.append('Ctrl')
    if modifiers & wx.MOD_SHIFT:
        lst.append('Shift')
    if modifiers & wx.MOD_ALT:
        lst.append('Alt')
    return '+'.join(lst)

def ConvertFlagsToModifiers(flags: wx.AcceleratorEntryFlags) -> wx.KeyModifier:
    modifiers = 0
    if flags & wx.ACCEL_CTRL:
        modifiers |= wx.MOD_CONTROL
    if flags & wx.ACCEL_SHIFT:
        modifiers |= wx.MOD_SHIFT
    if flags & wx.ACCEL_ALT:
        modifiers |= wx.MOD_ALT
    if flags & wx.ACCEL_CMD and wx.MOD_CMD == wx.MOD_META:
        modifiers |= wx.MOD_CMD
    return modifiers

def ConvertModifiersToFlags(modifiers: wx.KeyModifier) -> wx.AcceleratorEntryFlags:
    flags = 0
    if modifiers & wx.MOD_CONTROL:
        flags |= wx.ACCEL_CTRL
    if modifiers & wx.MOD_SHIFT:
        flags |= wx.ACCEL_SHIFT
    if modifiers & wx.MOD_ALT:
        flags |= wx.ACCEL_ALT
    if modifiers & wx.MOD_CMD and wx.MOD_CMD == wx.MOD_META:
        flags |= wx.ACCEL_CMD
    return flags


class HotkeyUpdatedEvent(wx.PyCommandEvent):
    """Custom wx event. Will be fired by the HotkeyCtrl onkeydown"""
    def __init__(self, ide: int, name: str, key_code: int, modifiers: wx.KeyModifier, obj=None):
        wx.PyCommandEvent.__init__(self, wxEVT_COMMAND_HOTKEY_UPDATED, ide)

        self._name = name
        self._key_code = key_code
        self._modifiers = modifiers
        self.SetEventObject(obj)
        
    def GetHotkeyName(self):
        return self._name

    def GetKeyCode(self):
        return self._key_code
    
    def GetModifiers(self):
        return self._modifiers
    
    def GetAcceleratorFlags(self):
        return ConvertModifiersToFlags(self._modifiers)
    

class HotkeyCtrl(wx.TextCtrl):
    """Custom control. Variant of TextCtrl that displays the inputted key (combination) instead of normal text."""
    def __init__(self, parent, ide=-1, default_value='', pos=wx.DefaultPosition,
                 size=wx.DefaultSize, style=0, name='hotkey'):
        #There appears to be no way to disable highlighting the text.
        style |= wx.TE_PROCESS_TAB | wx.TE_PROCESS_ENTER
        wx.TextCtrl.__init__(self, parent, ide, default_value, pos, size, style, name=name)
        self.Bind(wx.EVT_KEY_DOWN, self.OnKeyDown)
        self.Bind(wx.EVT_CHAR, self.OnChar)
        self._key_code: int|None = None
        self._modifiers: wx.KeyModifier|None = None
        self._default_value = default_value
        self._name = ''
        
    def Clear(self):
        self._key_code = self._modifiers = None
        self._name = ''
        self.SetValue(self._default_value)
    
    def OnKeyDown(self, event: wx.KeyEvent):
        name = GetHotkeyName(event.GetKeyCode(), event.GetModifiers())
        self.SetValue(name)
        self._name = name
        if event.GetKeyCode() != self._key_code or event.GetModifiers() != self._modifiers:
            self._key_code = event.GetKeyCode()
            self._modifiers = event.GetModifiers()
            self.GetEventHandler().ProcessEvent(
                HotkeyUpdatedEvent(self.GetId(), self._name, self._key_code,
                                   self._modifiers, self))
        event.Skip(False)
        
    def OnChar(self, event: wx.KeyEvent):
        event.Skip(False)
        
    def IsOk(self) -> bool:
        return self._key_code is not None

    def GetKeyCode(self):
        return self._key_code
    
    def GetModifiers(self):
        return self._modifiers
    
    def GetAcceleratorFlags(self):
        return ConvertModifiersToFlags(self._modifiers)

    def GetHotkeyName(self):
        return self._name


if __name__ == '__main__':
    class MyDialog(wx.Dialog):
        def __init__(self, *args, **kwds):
            # begin wxGlade: MyDialog.__init__
            kwds["style"] = wx.DEFAULT_DIALOG_STYLE
            wx.Dialog.__init__(self, *args, **kwds)
            style = wx.TE_PROCESS_TAB | wx.TE_PROCESS_ENTER
            self.txt = HotkeyCtrl(self, -1)
            self.txt.Bind(EVT_HOTKEY, self.on_hotkey_changed)
    
            sizer_6 = wx.BoxSizer(wx.HORIZONTAL)
            sizer_6.Add(self.txt, 0, 0, 0)
            self.SetSizer(sizer_6)
            sizer_6.Fit(self)
            self.Layout()
            
        def on_hotkey_changed(self, event):
            print(event.GetHotkeyName())
    
    app = wx.App(False)
    dlg = MyDialog(None)
    dlg.ShowModal()
