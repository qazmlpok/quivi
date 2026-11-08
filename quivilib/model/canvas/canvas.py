from quivilib.model.canvas.basecanvas import BaseCanvas


class Canvas(BaseCanvas):
    def __init__(self, settings, oldobj: BaseCanvas|None = None) -> None:
        super().__init__('canvas', settings, oldobj)
