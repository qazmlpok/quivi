class MockImage(object):
    def __init__(self):
        self.base_width = self.base_height = self.width = self.height = 0
    def SetDim(self, width, height):
        self.base_width = self.width = width
        self.base_height = self.height = height
    def resize_by_factor(self, factor: float) -> None:
        self.width = int(self.base_width * factor)
        self.height = int(self.base_height * factor)
    def rotate(self, clockwise: int) -> None:
        #Clockwise/not doesn't matter. There's no rotate 180 option.
        self.width, self.height = (self.height, self.width)
