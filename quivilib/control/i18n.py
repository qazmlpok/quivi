import sys
import logging as log
import locale
import traceback
from pathlib import Path

import wx
from pubsub import pub as Publisher


class I18NController(object):
    def __init__(self, control, settings):
        self.control = control
        self.settings = settings
        
        if sys.platform == 'win32':
            wx.Locale.AddCatalogLookupPathPrefix(str(self.control.localization_path))
        
        lang_code = settings.get('Language', 'ID')
        if lang_code == 'default':
            lang_code = wx.LANGUAGE_DEFAULT
        language = wx.LANGUAGE_ENGLISH_US
        for ide in self.available_languages:
            if wx.Locale.GetLanguageInfo(ide).CanonicalName == lang_code:
                language = ide
                break
        
        self.locale = None
        self.language = language
        
    def set_language(self, lang_id):
        info = wx.Locale.GetLanguageInfo(lang_id)
        if not info:
            return
 
        if self.locale:
            assert sys.getrefcount(self.locale) <= 2
            del self.locale
        
        #There's a bug with wx and/or Python3 where the locale is being set to "en-US",
        #which is invalid. Need to explicitly re-set the locale or it'll explode when it
        #next calls strptime or anything else involving locale.
        lang = info.GetLocaleName().replace("-", "_")
        self.locale = wx.Locale(lang_id)
        locale.setlocale(locale.LC_ALL, lang)
        if self.locale.IsOk():
            if sys.platform == 'win32':
                res = self.locale.AddCatalog(info.CanonicalName)
            else:
                res = self.locale.AddCatalog('quivi')
            self._language = lang_id
            self.settings.set('Language', 'ID', info.CanonicalName)
        else:
            self.locale = None
            self._language = wx.LANGUAGE_ENGLISH_US
            info = wx.Locale.GetLanguageInfo(self._language)
            self.settings.set('Language', 'ID', info.CanonicalName)
        
        Publisher.sendMessage('language.changed')

    def get_laguage(self):
        return self._language
    
    language = property(get_laguage, set_language)

    @property
    def available_languages(self):
        langs = []
        for name in wx.__dict__:
            if name.startswith('LANGUAGE_'):
                lang_id = wx.__dict__[name]
                lang_info = wx.Locale.GetLanguageInfo(lang_id)
                if lang_info is not None and lang_id != wx.LANGUAGE_DEFAULT:
                    lang_code = lang_info.CanonicalName
                    if sys.platform == 'win32':
                        path = self.control.localization_path / (lang_code + '.mo')
                    else:
                        path = Path('/usr') / 'share' / 'locale' / lang_code / 'LC_MESSAGES' / 'quivi.mo' 
                    try:
                        if path.exists():
                            langs.append(lang_id)
                    except IOError:
                        log.error(traceback.format_exc())
        if wx.LANGUAGE_ENGLISH_US not in langs:
            langs.append(wx.LANGUAGE_ENGLISH_US)
        return langs
