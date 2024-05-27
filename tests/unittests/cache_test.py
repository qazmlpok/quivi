

import unittest
import time

from pathlib import Path
from quivilib.model.container.directory import DirectoryContainer
from quivilib.model.container import SortOrder
from quivilib.model.settings import Settings
from quivilib.control.cache import ImageCache, ImageCacheLoadRequest

from pubsub import pub as Publisher
import wx
import time

import logging
logging.getLogger().setLevel(logging.NOTSET)



class Test(unittest.TestCase):
    def test_cache(self):
        app = wx.App(False)
        container = DirectoryContainer(Path('.') / 'tests' / 'dummy', SortOrder.TYPE, False)
        class Dummy:
            width = 800
            height = 600
        req = ImageCacheLoadRequest(container, container.items[2])
        s = Settings('filethatdoesnotexist.ini')
        cache = ImageCache(s)
        
        Publisher.sendMessage('cache.load_image', request=req)
        #Publisher.sendMessage('cache.load_image', request=req)
        
        #time.sleep(10)
        
        Publisher.sendMessage('program.closed')
