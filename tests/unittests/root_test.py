from __future__ import with_statement, absolute_import

import unittest
import sys

from quivilib.i18n import _
from quivilib.model.container.root import RootContainer
from quivilib.model.container import SortOrder
from quivilib.model.container.directory import DirectoryContainer
from quivilib.thirdparty.path import path as Path



class Test(unittest.TestCase):    
    def setUp(self):
        if sys.platform != 'win32':
            self.dir = None
        else:
            self.dir = RootContainer(SortOrder.TYPE)
        
        
    def test_refresh(self):
        if self.dir is None:
            return
        old_count = self.dir.item_count
        oldselected = self.dir.selected_item
           
        self.dir.refresh()
        
        self.assertEqual(old_count, self.dir.item_count)
        if oldselected:
            self.assertEqual(oldselected[0], self.dir.selected_item[0])
        else:
            self.assertEqual(oldselected, self.dir.selected_item)
        
    def test_sort_order_name(self):
        if self.dir is None:
            return
        self.dir.sort_order = SortOrder.NAME
    
    def test_sort_order_ext(self):
        if self.dir is None:
            return
        self.dir.sort_order = SortOrder.EXTENSION
    
    def test_sort_order_type(self):
        if self.dir is None:
            return
        self.dir.sort_order = SortOrder.TYPE
        
    def testselected_item(self):
        if self.dir is None:
            return
        item = self.dir.items[1]
        self.dir.selected_item = item
        self.dir.refresh()
        self.assertEquals(self.dir.selected_item, item)
        
    def test_name(self):
        if self.dir is None:
            return
        self.assertEquals(self.dir.name, _('My Computer'))
        
    def test_item_count(self):
        if self.dir is None:
            return
        self.dir.item_count
        
    def test_open_parent(self):
        if self.dir is None:
            return
        parent = self.dir.open_parent()
        self.assertTrue(parent is None)
        
    def test_get_item_name(self):
        if self.dir is None:
            return
        self.dir.sort_order = SortOrder.EXTENSION
        lst = [self.dir.get_item_name(i) for i in xrange(self.dir.item_count)]
        
    def test_get_item_extension(self):
        if self.dir is None:
            return
        self.dir.sort_order = SortOrder.EXTENSION
        lst = [self.dir.get_item_extension(i) for i in xrange(self.dir.item_count)]
        
    def test_set_selection(self):
        if self.dir is None:
            return
        self.dir.selected_item = 1
        self.assertEquals(self.dir.items.index(self.dir.selected_item), 1)
        self.dir.selected_item = self.dir.items[1]
        self.assertEquals(self.dir.selected_item, self.dir.items[1])
        
    def test_path(self):
        if self.dir is None:
            return
        self.assertEquals(self.dir.path, '')
    