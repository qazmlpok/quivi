

import unittest

from quivilib.model.settings import Settings



class Test(unittest.TestCase):
    def test_defaults(self):
        s = Settings('filethatdoesnotexist.ini')
        self.assertEqual(s.getint('Options', 'FitWidthCustomSize'), 800)
        