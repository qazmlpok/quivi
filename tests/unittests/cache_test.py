from __future__ import with_statement, absolute_import

import unittest
import time

from quivilib.thirdparty.path import path as Path
from quivilib.model.container.directory import DirectoryContainer
from quivilib.model.container import SortOrder
from quivilib.model.settings import Settings
from quivilib.control.cache import ImageCache, ImageCacheLoadRequest

from wx.lib.pubsub import pub as Publisher
import wx
import time

import logging
logging.getLogger().setLevel(logging.NOTSET)



class Test(unittest.TestCase):
    def test_cache(self):
        app = wx.App(False)
        container = DirectoryContainer(Path(u'.') / 'tests' / 'dummy', SortOrder.TYPE)
        class Dummy:
            width = 800
            height = 600
        req = ImageCacheLoadRequest(container, container.items[2], Dummy())
        s = Settings('filethatdoesnotexist.ini')
        cache = ImageCache(s)
        
        Publisher.sendMessage('cache.load_image', req)
        #Publisher.sendMessage('cache.load_image', req)
        
        #time.sleep(10)
        
        Publisher.sendMessage('program.closed', None)
