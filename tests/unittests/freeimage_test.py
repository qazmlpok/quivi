import os.path
import unittest

import wx

import pyfreeimage as fi


class Test(unittest.TestCase):
    
    def setUp(self):
        self.lib = fi.library.load()
        self.app = wx.App()
        
    def test_get_readable_fifs(self):
        fifs = self.lib.get_readable_fifs()
        self.assertTrue(len(fifs) > 0)
        
    def test_get_readable_extensions(self):
        exts = self.lib.get_readable_extensions()
        self.assertTrue('.jpg' in exts)
        
    def test_get_readable_extensions_descriptions(self):
        dic = self.lib.get_readable_extensions_descriptions()
        self.assertTrue(len(dic) > 0)
        self.assertTrue('.jpg' in dic)
        
    def test_convert_wx(self):
        self.assertFalse(os.path.exists('./tests/out/python.bmp'))
        img = fi.Image.load('./tests/python.png')
        bmp = img.convert_to_wx_bitmap(wx)
        bmp.SaveFile('./tests/out/python.bmp', wx.BITMAP_TYPE_BMP)
        self.assertTrue(os.path.exists('./tests/out/python.bmp'))
