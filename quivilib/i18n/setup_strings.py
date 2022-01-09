
"""Setup strings.

This module exists only to make the .po file include the strings
used in the setup, so translators need only to work on one file.

It also writes the correct include file for the nsis setup script
when run.
"""
import wx
from wx.lib.pubsub import setuparg1

from quivilib.i18n import _
from quivilib.control.i18n import I18NController
from pathlib import Path



if __name__ == '__main__':
    app = wx.PySimpleApp()
    class DummyControl():
        localization_path = Path('./localization/')
    class DummySettings():
        def get(self, section, option):
            return 'default'
        def set(self, section, option, value):
            pass
    
    c = I18NController(DummyControl(), DummySettings())
    
    lang_names = {
                  wx.LANGUAGE_ENGLISH_US: 'English',
                  wx.LANGUAGE_PORTUGUESE_BRAZILIAN: 'PortugueseBR',
                  wx.LANGUAGE_SPANISH_MEXICAN: 'Spanish',
                  wx.LANGUAGE_POLISH: 'Polish',
                  wx.LANGUAGE_RUSSIAN: 'Russian',
    }

    header = ""
    body = ""
    for lang in c.available_languages:
        if lang not in lang_names:
            continue
        c.language = lang
        lang_name = lang_names[lang]
        
        header += '!insertmacro MUI_LANGUAGE "%s"\n' % lang_name
        
        TEXT_LANG = _("en_US")
        TEXT_USER_TITLE = _("Select users")
        TEXT_USER_SUBTITLE = _("Select for which users you want to install $(^Name)")
        TEXT_USER_ALLUSERS = _("All users")
        TEXT_USER_CURRENTUSER = _("Current user")
        TEXT_COMPONENT_APP = _("$(^Name) (required)")
        TEXT_COMPONENT_STARTMENU = _("Start Menu Group")
        TEXT_COMPONENT_DESKTOP = _("Desktop Shortcut")
        TEXT_COMPONENT_ASSOCIATE = _("Associate extensions")
        
        lcls = locals().copy()
        for var in lcls:
            if var.startswith('TEXT_'):
                body += 'LangString %s ${LANG_%s} "%s"\n' % (var, lang_name.upper(), lcls[var])
                
        body += '\n'
    
    ENCODING = 'utf_16'
    txt = header + '\n\n' + body
    with open('./localization/setup_strings.nsh', 'wb') as f:
        f.write(txt.encode(ENCODING))
