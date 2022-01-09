

import unittest
import sys

import quivilib.util as U


class Test(unittest.TestCase):
        
    def test_scale_by_size_factor(self):
        self.assertAlmostEqual(U.rescale_by_size_factor(50, 50, 100, 100), 2, 3)
        self.assertAlmostEqual(U.rescale_by_size_factor(50, 50, 0, 100), 2, 3)
        self.assertAlmostEqual(U.rescale_by_size_factor(50, 50, 100, 0), 2, 3)
        self.assertAlmostEqual(U.rescale_by_size_factor(100, 100, 50, 50), 0.5, 3)
        self.assertAlmostEqual(U.rescale_by_size_factor(100, 100, 50, 80), 0.5, 3)
        self.assertAlmostEqual(U.rescale_by_size_factor(100, 100, 80, 50), 0.5, 3)
        self.assertAlmostEqual(U.rescale_by_size_factor(100, 100, 50, 0), 0.5, 3)
        self.assertAlmostEqual(U.rescale_by_size_factor(100, 100, 0, 50), 0.5, 3)
        self.assertAlmostEqual(U.rescale_by_size_factor(200, 100, 100, 100), 0.5, 3)
        self.assertAlmostEqual(U.rescale_by_size_factor(100, 200, 100, 100), 0.5, 3)
        self.assertAlmostEqual(U.rescale_by_size_factor(500, 100, 100, 0), 0.2, 3)
        self.assertAlmostEqual(U.rescale_by_size_factor(500, 100, 100, 50), 0.2, 3)
        self.assertAlmostEqual(U.rescale_by_size_factor(500, 100, 100, 10), 0.1, 3)
        self.assertAlmostEqual(U.rescale_by_size_factor(500, 100, 0, 0), 1, 3)
        
    def test_add_exception_info(self):
        try:
            try:
                raise Exception('foo')
            except Exception as e:
                U.add_exception_info(e, 'bar')
                raise
        except Exception as e:
            self.assertEqual(e.get_custom_msg(), 'bar\n(foo)')
    
    def test_add_exception_custom_msg(self):
        try:
            try:
                raise Exception('foo')
            except Exception as e:
                U.add_exception_custom_msg(e, 'bar')
                raise
        except Exception as e:
            self.assertEqual(e.get_custom_msg(), 'bar')
            
    def test_get_ext_path(self):
        self.assertTrue(U.get_exe_path())
    
    def test_is_frozen(self):
        self.assertTrue(U.is_frozen() in (True, False))