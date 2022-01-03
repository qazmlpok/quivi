from __future__ import with_statement, absolute_import

import unittest

from quivilib.model.settings import Settings



class Test(unittest.TestCase):
    def test_defaults(self):
        s = Settings('filethatdoesnotexist.ini')
        self.assertEquals(s.getint('Options', 'FitWidthCustomSize'), 800)
        