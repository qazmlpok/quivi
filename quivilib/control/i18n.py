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

        # I do not understand localization. Or Linux. The folder is `localization`. Should it be, or is `locale` correct?
        if sys.platform == 'win32' or __debug__:
            wx.Locale.AddCatalogLookupPathPrefix(str(self.control.localization_path))

        lang_code = settings.get('Language', 'ID')
        if lang_code == 'default':
            lang_code = wx.LANGUAGE_DEFAULT
        lang = wx.LANGUAGE_ENGLISH_US
        for ide in self.available_languages:
            if wx.Locale.GetLanguageInfo(ide).CanonicalName == lang_code:
                lang = ide
                break

        self.locale = None
        self.language = lang

    @property
    def language(self):
        return self._language
    @language.setter
    def language(self, lang_id):
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
            res = self.locale.AddCatalog('quivi')
            self._language = lang_id
            self.settings.set('Language', 'ID', info.CanonicalName)
        else:
            self.locale = None
            self._language = wx.LANGUAGE_ENGLISH_US
            info = wx.Locale.GetLanguageInfo(self._language)
            self.settings.set('Language', 'ID', info.CanonicalName)

        Publisher.sendMessage('language.changed')

    @property
    def available_languages(self):
        langs = []

        # Note - This will add the language to the list even if it isn't installed.
        # It won't be possible to switch to the language even though it's in the list. There's probably a way to fix this...
        def try_add_lang(path: Path, language_id):
            try:
                if path.exists():
                    langs.append(language_id)
            except IOError:
                log.error(traceback.format_exc())

        for name in wx.__dict__:
            if name.startswith('LANGUAGE_'):
                lang_id = wx.__dict__[name]
                lang_info = wx.Locale.GetLanguageInfo(lang_id)
                if lang_info is not None and lang_id != wx.LANGUAGE_DEFAULT:
                    lang_code = lang_info.CanonicalName
                    if sys.platform == 'win32' or __debug__:
                        try_add_lang(self.control.localization_path / lang_code / 'LC_MESSAGES' / 'quivi.mo', lang_id)
                    if sys.platform != 'win32':
                        try_add_lang(Path('/usr') / 'share' / 'locale' / lang_code / 'LC_MESSAGES' / 'quivi.mo', lang_id)
        if wx.LANGUAGE_ENGLISH_US not in langs:
            langs.append(wx.LANGUAGE_ENGLISH_US)
        return langs
