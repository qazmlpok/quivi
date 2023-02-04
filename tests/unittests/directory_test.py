

import unittest

from quivilib.model.container import SortOrder
from quivilib.model.container.directory import DirectoryContainer
from quivilib.model.container.compressed import CompressedContainer
from pathlib import Path



class Test(unittest.TestCase):
    def setUp(self):
        self.dir = DirectoryContainer(Path('./tests/dummy'), SortOrder.TYPE, False)
    
    def test_refresh(self):
        old_count = self.dir.item_count
        oldselected = self.dir.selected_item
           
        self.dir.refresh(False)
        
        self.assertEqual(old_count, self.dir.item_count)
        if oldselected:
            self.assertEqual(oldselected[0], self.dir.selected_item[0])
        else:
            self.assertEqual(oldselected, self.dir.selected_item)
        
    def test_sort_order_name(self):
        self.dir.sort_order = SortOrder.NAME
        lst = [item.name for item in self.dir.items]
        self.assertEqual(lst, ['..', 'ateste.zip', 'dir', 'teste.jpg', 'wteste.gif'])
    
    def test_sort_order_ext(self):
        self.dir.sort_order = SortOrder.EXTENSION
        lst = [item.name for item in self.dir.items]
        self.assertEqual(lst, ['..', 'dir', 'wteste.gif', 'teste.jpg', 'ateste.zip'])
    
    def test_sort_order_type(self):
        self.dir.sort_order = SortOrder.TYPE
        lst = [item.name for item in self.dir.items]
        self.assertEqual(lst, ['..', 'dir', 'teste.jpg', 'wteste.gif', 'ateste.zip'])
    
    def test_sort_numbers(self):
        self.dir = DirectoryContainer(Path('./tests/Order'), SortOrder.NAME, False)
        self.dir.sort_order = SortOrder.NAME
        lst = [item.name for item in self.dir.items]
        self.assertEqual(lst, ['..', 
                '1.png', '1a.png', '2.png', '2a.png', '8.png', '8a.png', '9.png', '9a.png', 
                '10.png', '10a.png', '11.png', '11a.png', 'a9.png', 'a10.png', 'a11.png', 
        ])
        
    def test_sort_numbers_nested(self):
        #This needs to use a zip file because a dir container won't include sub-files
        self.dir = CompressedContainer(Path('./tests/Order_nested.zip'), SortOrder.NAME, False)
        self.dir.sort_order = SortOrder.NAME
        lst = [item.path for item in self.dir.items]
        #Use a Path object to avoid \ / issues.
        fnames = ['1.png', '2.png', '8.png', '9.png', '10.png', '11.png']
        dirs = ['c1', 'c2']
        paths = [Path('..')]
        for dname in dirs:
            for fname in fnames:
                paths.append(Path(dname) / fname)
        self.assertEqual(lst, paths)
        
    
    def testselected_item(self):
        item = self.dir.items[1]
        self.dir.selected_item = item
        self.dir.refresh(False)
        self.assertEqual(self.dir.selected_item, item)
        
    def test_name(self):
        self.assertEqual(self.dir.name, 'dummy')
        
    def test_item_count(self):
        self.assertEqual(self.dir.item_count, 5)
        
    def test_open_parent(self):
        parent = self.dir.open_parent()
        self.assertEqual(parent.path, self.dir.path.parent)
        self.assertEqual(parent.selected_item.path, self.dir.path)
        
    def test_get_item_name(self):
        self.dir.sort_order = SortOrder.EXTENSION
        lst = [self.dir.get_item_name(i) for i in range(self.dir.item_count)]
        self.assertEqual(lst, ['..', 'dir', 'wteste.gif', 'teste.jpg', 'ateste.zip'])
        
    def test_get_item_extension(self):
        self.dir.sort_order = SortOrder.EXTENSION
        lst = [self.dir.get_item_extension(i) for i in range(self.dir.item_count)]
        self.assertEqual(lst, ['', '', 'gif', 'jpg', 'zip'])
        
    def test_set_selection(self):
        self.dir.selected_item = 1
        self.assertEqual(self.dir.items.index(self.dir.selected_item), 1)
        self.dir.selected_item = self.dir.items[1]
        self.assertEqual(self.dir.selected_item, self.dir.items[1])