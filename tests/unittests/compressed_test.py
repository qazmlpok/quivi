

import unittest

from quivilib.model.container import SortOrder
from quivilib.model.container.compressed import CompressedContainer
from pathlib import Path



class Test(unittest.TestCase):
    def setUp(self):
        self.zip = CompressedContainer(Path('./tests/dummy.zip'), SortOrder.TYPE, False)
        self.rar = CompressedContainer(Path('./tests/dummy.rar'), SortOrder.TYPE, False)
    
    def test_refresh_zip(self):
        old_count = self.zip.item_count
        oldselected = self.zip.selected_item

        self.zip.refresh(False)
        
        self.assertEqual(old_count, self.zip.item_count)
        if oldselected:
            self.assertEqual(oldselected[0], self.zip.selected_item[0])
        else:
            self.assertEqual(oldselected, self.zip.selected_item)
    
    def test_refresh_rar(self):
        old_count = self.rar.item_count
        oldselected = self.rar.selected_item

        self.rar.refresh(False)
        
        self.assertEqual(old_count, self.rar.item_count)
        if oldselected:
            self.assertEqual(oldselected[0], self.rar.selected_item[0])
        else:
            self.assertEqual(oldselected, self.rar.selected_item)
        
    def test_sort_order_name(self):
        self.zip.sort_order = SortOrder.NAME
        lst = [item.name for item in self.zip.items]
        self.assertEqual(lst, ['..', 'ateste.zip', 'teste.jpg', 'wteste.gif'])
    
    def test_sort_order_ext(self):
        self.zip.sort_order = SortOrder.EXTENSION
        lst = [item.name for item in self.zip.items]
        self.assertEqual(lst, ['..', 'wteste.gif', 'teste.jpg', 'ateste.zip'])
    
    def test_sort_order_type(self):
        self.zip.sort_order = SortOrder.TYPE
        lst = [item.name for item in self.zip.items]
        self.assertEqual(lst, ['..', 'teste.jpg', 'wteste.gif', 'ateste.zip'])
        
    def testselected_item(self):
        item = self.zip.items[1]
        self.zip.selected_item = item
        self.zip.refresh(False)
        self.assertEqual(self.zip.selected_item, item)
        
    def test_name(self):
        self.assertEqual(self.zip.name, 'dummy.zip')
        
    def test_item_count(self):
        self.assertEqual(self.zip.item_count, 4)
        
    def test_open_parent(self):
        parent = self.zip.open_parent()
        self.assertEqual(parent.path, self.zip.path.parent)
        self.assertEqual(parent.selected_item.path, self.zip.path)
        
    def test_get_item_name(self):
        self.zip.sort_order = SortOrder.EXTENSION
        lst = [self.zip.get_item_name(i) for i in range(self.zip.item_count)]
        self.assertEqual(lst, ['..', 'dummy/wteste.gif', 'dummy/teste.jpg', 'dummy/ateste.zip'])
        
    def test_get_item_extension(self):
        self.zip.sort_order = SortOrder.EXTENSION
        lst = [self.zip.get_item_extension(i) for i in range(self.zip.item_count)]
        self.assertEqual(lst, ['', 'gif', 'jpg', 'zip'])
        
    def test_set_selection(self):
        self.zip.selected_item = 1
        self.assertEqual(self.zip.items.index(self.zip.selected_item), 1)
        self.zip.selected_item = self.zip.items[1]
        self.assertEqual(self.zip.selected_item, self.zip.items[1])
        
    def test_open_image_zip(self):
        self.zip.sort_order = SortOrder.TYPE
        img = self.zip.open_image(1).read()
        img_ref = open('./tests/dummy/wteste.gif', 'rb').read()
        self.assertEqual(img, img_ref)
        
    def test_open_image_rar(self):
        self.rar.sort_order = SortOrder.TYPE
        img = self.rar.open_image(1).read()
        img_ref = open('./tests/dummy/wteste.gif', 'rb').read()
        self.assertEqual(img, img_ref)