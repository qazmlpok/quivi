

import unittest

from quivilib.model.commandenum import FitSettings
from quivilib.model.settings import Settings


class Test(unittest.TestCase):
    def test_defaults(self):
        s = Settings('filethatdoesnotexist.ini')
        self.assertEqual(s.getint('Options', 'FitWidthCustomSize'), 800)

    def test_oldfitsettings(self):
        tst = FitSettings.get_fittype(FitSettings.OldValues.FIT_NONE)
        self.assertEqual(tst, FitSettings.FitType.NONE)
        tst = FitSettings.get_fittype(FitSettings.OldValues.FIT_WIDTH_OVERSIZE)
        self.assertEqual(tst, FitSettings.FitType.WIDTH_IF_LARGER)
        tst = FitSettings.get_fittype(FitSettings.OldValues.FIT_HEIGHT_OVERSIZE)
        self.assertEqual(tst, FitSettings.FitType.HEIGHT_IF_LARGER)
        tst = FitSettings.get_fittype(FitSettings.OldValues.FIT_BOTH_OVERSIZE)
        self.assertEqual(tst, FitSettings.FitType.WINDOW_IF_LARGER)
        tst = FitSettings.get_fittype(FitSettings.OldValues.FIT_CUSTOM_WIDTH)
        self.assertEqual(tst, FitSettings.FitType.CUSTOM_WIDTH)
        tst = FitSettings.get_fittype(FitSettings.OldValues.FIT_WIDTH)
        self.assertEqual(tst, FitSettings.FitType.WIDTH)
        tst = FitSettings.get_fittype(FitSettings.OldValues.FIT_HEIGHT)
        self.assertEqual(tst, FitSettings.FitType.HEIGHT)
        tst = FitSettings.get_fittype(FitSettings.OldValues.FIT_BOTH)
        self.assertEqual(tst, FitSettings.FitType.WINDOW)

        tst = FitSettings.get_fittype(FitSettings.OldValues.FIT_BOTH + 1)
        self.assertEqual(tst, FitSettings.FitType.NONE)

    def test_fitsettings(self):
        #224 = FitSettings.FitType.WINDOW, 480 = FitSettings.FitType.WINDOW_IF_LARGER. This is expected to work but shouldn't be necessary
        #and the values could change at any time.
        tst = FitSettings.get_fittype('WINDOW')
        self.assertEqual(tst, FitSettings.FitType.WINDOW)
        tst = FitSettings.get_fittype('FitType.WINDOW')
        self.assertEqual(tst, FitSettings.FitType.WINDOW)
        tst = FitSettings.get_fittype(224)
        self.assertEqual(tst, FitSettings.FitType.WINDOW)

        tst = FitSettings.get_fittype('WINDOW_IF_LARGER')
        self.assertEqual(tst, FitSettings.FitType.WINDOW_IF_LARGER)
        tst = FitSettings.get_fittype('FitType.WINDOW_IF_LARGER')
        self.assertEqual(tst, FitSettings.FitType.WINDOW_IF_LARGER)
        tst = FitSettings.get_fittype(480)
        self.assertEqual(tst, FitSettings.FitType.WINDOW_IF_LARGER)

        tst = FitSettings.get_fittype(str(FitSettings.FitType.WINDOW_IF_LARGER))
        self.assertEqual(tst, FitSettings.FitType.WINDOW_IF_LARGER)
        tst = FitSettings.get_fittype(FitSettings.FitType.WINDOW_IF_LARGER.value)
        self.assertEqual(tst, FitSettings.FitType.WINDOW_IF_LARGER)
