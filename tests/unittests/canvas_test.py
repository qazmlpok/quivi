import unittest

from quivilib.model.canvas.canvas import Canvas
from quivilib.model.canvas.wallpapercanvas import WallpaperCanvas
from quivilib.model.commandenum import FitSettings
from quivilib.model.settings import Settings
from tests.unittests.mock.mock_image import MockImage


class Test(unittest.TestCase):
    def setUp(self):
        self.c = Canvas(Settings('invalidfile'))
        class View(object):
            def __init__(self):
                self.width = self.height = 0
        self.v = View()
        self.c.set_view(self.v)
        self.im = MockImage()
        self.c.img = self.im

    def test_accessors(self):
        self.v.width = 700
        self.v.height = 500
        self.im.width = 200
        self.im.height = 300

        self.assertEqual(self.c.view_width, 700)
        self.assertEqual(self.c.view_height, 500)
        self.assertEqual(self.c.width, 200)
        self.assertEqual(self.c.height, 300)

    def test_left_top_view_larger(self):
        #View larger than the image - top/left constrained to [0, view-img]
        self.v.width = 700
        self.v.height = 500
        self.im.width = 200
        self.im.height = 300

        self.assertEqual(self.c.top, 0)
        self.assertEqual(self.c.left, 0)

        self.c.left = 100000
        self.assertEqual(self.c.left, (self.v.width - self.im.width))
        self.c.top = 100000
        self.assertEqual(self.c.top, (self.v.height - self.im.height))

        self.c.left = -99999
        self.assertEqual(self.c.left, 0)
        self.c.top = -99999
        self.assertEqual(self.c.top, 0)

        self.c.left = self.c.top = 100
        self.assertEqual(self.c.left, 100)
        self.assertEqual(self.c.top, 100)

    def test_left_top_equal(self):
        #View and image same size: top/left can only be zero.
        self.v.width = self.v.height = self.im.width = self.im.height = 100

        self.c.left = 1
        self.c.top = 1
        self.assertEqual(self.c.top, 0)
        self.assertEqual(self.c.left, 0)

        self.c.left = -1
        self.c.top = -1
        self.assertEqual(self.c.top, 0)
        self.assertEqual(self.c.left, 0)

    def test_left_top_view_smaller(self):
        #View smaller than the image - top/left constrained to [view-img, 0] (i.e. negative or 0)
        self.v.width = 200
        self.v.height = 300
        self.im.width = 500
        self.im.height = 700

        self.assertEqual(self.c.top, 0)
        self.assertEqual(self.c.left, 0)

        self.c.left = 100000
        self.assertEqual(self.c.left, 0)
        self.c.top = 100000
        self.assertEqual(self.c.top, 0)

        self.c.left = -99999
        self.assertEqual(self.c.left, (self.v.width - self.im.width))
        self.c.top = -99999
        self.assertEqual(self.c.top, (self.v.height - self.im.height))

        self.c.left = self.c.top = -100
        self.assertEqual(self.c.left, -100)
        self.assertEqual(self.c.top, -100)

    def test_rotate_view_larger(self):
        #Rotation is a visual check. If the image is smaller than the canvas, it should rotate around the center of the image.
        #Rotating 4 times returns you to the start, and cw + ccw undoes rotation. This can be checked.
        # Note that rotating sets left/top, not _left/_top. It will be constrained by the setter.
        top = 1000
        left = 2000
        self.v.width = 7000
        self.v.height = 5000
        self.im.width = 200
        self.im.height = 300
        self.c.top = top
        self.c.left = left
        assert self.c.top != 0
        assert self.c.left != 0

        self.c.rotate(1)
        self.assertNotEqual(self.c.top, top)
        self.assertNotEqual(self.c.left, left)
        self.c.rotate(0)    #...this needs to be a bool. Why isn't it?
        self.assertEqual(self.c.top, top)
        self.assertEqual(self.c.left, left)

        self.c.rotate(1)
        self.c.rotate(1)
        self.c.rotate(1)
        self.c.rotate(1)
        self.assertEqual(self.c.top, top)
        self.assertEqual(self.c.left, left)

    def test_rotate_view_smaller(self):
        #Rotation is a visual check. If the image is larger than the canvas, it should rotate around the center of the screen.
        #Rotating 4 times returns you to the start, and cw + ccw undoes rotation. This can be checked.
        # Note that rotating sets left/top, not _left/_top. It will be constrained by the setter.
        top = -1000
        left = -2000
        self.v.width = 700
        self.v.height = 500
        self.im.width = 20000
        self.im.height = 30000
        self.c.top = top
        self.c.left = left
        assert self.c.top != 0
        assert self.c.left != 0

        self.c.rotate(1)
        self.assertNotEqual(self.c.top, top)
        self.assertNotEqual(self.c.left, left)
        self.c.rotate(0)    #...this needs to be a bool. Why isn't it?
        self.assertEqual(self.c.top, top)
        self.assertEqual(self.c.left, left)

        self.c.rotate(1)
        self.c.rotate(1)
        self.c.rotate(1)
        self.c.rotate(1)
        self.assertEqual(self.c.top, top)
        self.assertEqual(self.c.left, left)

    def test_zoom(self):
        self.im.SetDim(800, 600)
        self.assertEqual(self.c.zoom, 1)
        self.c.zoom = 0
        self.assertEqual(self.c.zoom, 1)

        #Zooming will also adjust left/top. The only real way to validate this is to do it and see if it looks right.
        self.c.zoom = 2
        self.assertEqual(self.c.width, 1600)
        self.assertEqual(self.c.height, 1200)

        self.c.zoom = 0.5
        self.assertEqual(self.c.width, 400)
        self.assertEqual(self.c.height, 300)

        self.c.zoom_reset()
        self.assertEqual(self.c.zoom, 1)
        self.assertEqual(self.c.width, 800)
        self.assertEqual(self.c.height, 600)

    def test_zoom_fit(self):
        (self.v.width, self.v.height) = (800, 600)
        self.im.SetDim(1920, 1080)
        aspect_ratio = self.im.width / self.im.height
        def assert_aspect_ratio():
            t = self.im.width / self.im.height
            self.assertAlmostEqual(t, aspect_ratio, 2)

        #Can't do custom width without hooking up settings

        #Run the assert with and without _OVERSIZE. If the image is larger they are the same.
        def do_test_img_larger(fittype: int, fn):
            self.c.set_zoom_by_fit_type(fittype)
            fn()
            if fittype != FitSettings.FitType.NONE:
                self.assertNotEqual(self.c.zoom, 1)
                self.assertLess(self.c.zoom, 1)
            assert_aspect_ratio()
            self.c.zoom_reset()
            self.assertEqual(self.c.zoom, 1)
            self.c.set_zoom_by_fit_type(fittype & ~FitSettings.FitType._OVERSIZE)
            fn()
            if fittype != FitSettings.FitType.NONE:
                self.assertNotEqual(self.c.zoom, 1)
                self.assertLess(self.c.zoom, 1)
            assert_aspect_ratio()
            self.c.zoom_reset()

        do_test_img_larger(FitSettings.FitType.HEIGHT_IF_LARGER, lambda: self.assertEqual(self.im.height, 600))
        do_test_img_larger(FitSettings.FitType.WIDTH_IF_LARGER, lambda: self.assertEqual(self.im.width, 800))
        do_test_img_larger(FitSettings.FitType.WINDOW_IF_LARGER, lambda: self.assertEqual(self.im.width, 800))  #Scales by width
        do_test_img_larger(FitSettings.FitType.NONE, lambda: self.assertEqual(self.im.height, 1080))

        (self.v.width, self.v.height) = (1920, 1080)
        self.im.SetDim(800, 600)
        aspect_ratio = self.im.width / self.im.height

        # Run the assert with and without _OVERSIZE. With oversize nothing will happen.
        def do_test_img_smaller(fittype: int, fn):
            self.c.set_zoom_by_fit_type(fittype)
            self.assertEqual(self.c.zoom, 1)
            assert_aspect_ratio()
            self.c.zoom_reset()
            self.assertEqual(self.c.zoom, 1)
            self.c.set_zoom_by_fit_type(fittype & ~FitSettings.FitType._OVERSIZE)
            fn()
            if fittype != FitSettings.FitType.NONE:
                self.assertNotEqual(self.c.zoom, 1)
                self.assertGreater(self.c.zoom, 1)
            assert_aspect_ratio()
            self.c.zoom_reset()

        do_test_img_smaller(FitSettings.FitType.HEIGHT_IF_LARGER, lambda: self.assertEqual(self.im.height, 1080))
        do_test_img_smaller(FitSettings.FitType.WIDTH_IF_LARGER, lambda: self.assertEqual(self.im.width, 1920))
        do_test_img_smaller(FitSettings.FitType.WINDOW_IF_LARGER, lambda: self.assertEqual(self.im.height, 1080))   #Scales by height
        do_test_img_smaller(FitSettings.FitType.NONE, lambda: self.assertEqual(self.im.height, 600))


class WallpaperTest(unittest.TestCase):
    def setUp(self):
        self.c = WallpaperCanvas(Settings('invalidfile'))
        class View(object):
            def __init__(self):
                self.width = self.height = 0
        self.v = View()
        self.c.set_view(self.v)
        self.im = MockImage()
        self.c.img = self.im

    def test_center(self):
        self.v.width = self.v.height = 50
        self.im.width = self.im.height = 100
        self.c.center()

        self.assertEqual(self.c.top, 0)
        self.assertEqual(self.c.left, 0)
        # self.assertTrue(self.c.centered)   #centered does not function if the image is larger than the canvas. Should it?

        self.v.width = self.v.height = 150
        self.c.center()

        self.assertEqual(self.c.top, 25)
        self.assertEqual(self.c.left, 25)
        self.assertTrue(self.c.centered)
