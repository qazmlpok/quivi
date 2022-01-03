from __future__ import with_statement, absolute_import

import unittest

from quivilib.model.container import SortOrder
from quivilib.model.container.directory import DirectoryContainer
from quivilib.thirdparty.path import path as Path



class Test(unittest.TestCase):
    def setUp(self):
        self.dir = DirectoryContainer(Path(u'./tests/dummy'), SortOrder.TYPE)
    
    def test_refresh(self):
        old_count = self.dir.item_count
        oldselected = self.dir.selected_item
           
        self.dir.refresh()
        
        self.assertEqual(old_count, self.dir.item_count)
        if oldselected:
            self.assertEqual(oldselected[0], self.dir.selected_item[0])
        else:
            self.assertEqual(oldselected, self.dir.selected_item)
        
    def test_sort_order_name(self):
        self.dir.sort_order = SortOrder.NAME
        lst = [item.name for item in self.dir.items]
        self.assertEquals(lst, ['..', 'ateste.zip', 'dir', 'teste.jpg', 'wteste.gif'])
    
    def test_sort_order_ext(self):
        self.dir.sort_order = SortOrder.EXTENSION
        lst = [item.name for item in self.dir.items]
        self.assertEquals(lst, ['..', 'dir', 'wteste.gif', 'teste.jpg', 'ateste.zip'])
    
    def test_sort_order_type(self):
        self.dir.sort_order = SortOrder.TYPE
        lst = [item.name for item in self.dir.items]
        self.assertEquals(lst, ['..', 'dir', 'teste.jpg', 'wteste.gif', 'ateste.zip'])
        
    def testselected_item(self):
        item = self.dir.items[1]
        self.dir.selected_item = item
        self.dir.refresh()
        self.assertEquals(self.dir.selected_item, item)
        
    def test_name(self):
        self.assertEquals(self.dir.name, u'dummy')
        
    def test_item_count(self):
        self.assertEquals(self.dir.item_count, 5)
        
    def test_open_parent(self):
        parent = self.dir.open_parent()
        self.assertEquals(parent.path, self.dir.path.parent)
        self.assertEquals(parent.selected_item.path, self.dir.path)
        
    def test_get_item_name(self):
        self.dir.sort_order = SortOrder.EXTENSION
        lst = [self.dir.get_item_name(i) for i in xrange(self.dir.item_count)]
        self.assertEquals(lst, ['..', 'dir', 'wteste.gif', 'teste.jpg', 'ateste.zip'])
        
    def test_get_item_extension(self):
        self.dir.sort_order = SortOrder.EXTENSION
        lst = [self.dir.get_item_extension(i) for i in xrange(self.dir.item_count)]
        self.assertEquals(lst, ['', '', 'gif', 'jpg', 'zip'])
        
    def test_set_selection(self):
        self.dir.selected_item = 1
        self.assertEquals(self.dir.items.index(self.dir.selected_item), 1)
        self.dir.selected_item = self.dir.items[1]
        self.assertEquals(self.dir.selected_item, self.dir.items[1])