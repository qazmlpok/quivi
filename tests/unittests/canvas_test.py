from __future__ import with_statement, absolute_import

from quivilib.model.canvas import Canvas
from quivilib.model.settings import Settings

import unittest


class Test(unittest.TestCase):
    def setUp(self):
        self.c = Canvas('canvas', Settings('invalidfile'))
        class View(object):
            def __init__(self):
                self.width = self.height = 0
        class Image(object):
            def __init__(self):
                self.width = self.height = 0
        self.v = View()
        self.c.set_view(self.v)
        self.b = Image()
        self.c.img = self.b
        
    def test_center(self):
        self.v.width = self.v.height = 50
        self.b.width = self.b.height = 100
        self.c.center()
        self.assertEquals(self.c.top, 0)
        self.assertEquals(self.c.left, 0)
        
        self.v.width = self.v.height = 150
        self.c.center()
        
        self.assertEquals(self.c.top, 25)
        self.assertEquals(self.c.left, 25)
        