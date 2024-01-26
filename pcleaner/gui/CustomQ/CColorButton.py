import PySide6.QtWidgets as Qw
import PySide6.QtCore as Qc
import PySide6.QtGui as Qg


"""
Extend a PushButton to display a color, and allow the user to change it
with a color dialog.

The color is stored as a QColor object.
Optionally, use an alpha channel.

The color can be set or retrieved as a 3 or 4 tuple of ints.


The button has a custom painter that draws a rectangle with the color,
and if the color is None, it defaults to white.
If the color has an alpha channel, the rectangle is drawn with a checkerboard]
pattern behind it.
"""


# Follow Qt's naming convention of CamelCase for functions, signals, and classes
# noinspection PyPep8Naming
class ColorButton(Qw.QPushButton):
    colorChanged = Qc.Signal(Qg.QColor)

    def __init__(
        self,
        parent=None,
        color: tuple[int, int, int, int] | tuple[int, int, int] = (255, 255, 255, 255),
        dialog_title: str | None = None,
    ):
        super().__init__(parent)
        self._color: Qg.QColor = Qg.QColor(*color)
        self.use_alpha = len(color) == 4
        self.dialog_title = dialog_title if dialog_title else self.tr("Select Color")
        self.setFixedHeight(32)
        self.clicked.connect(self._open_color_dialog)

    def paintEvent(self, event: Qg.QPaintEvent) -> None:
        painter = Qg.QPainter(self)
        painter.setRenderHint(Qg.QPainter.Antialiasing)
        self._draw_color(painter)

    def _open_color_dialog(self) -> None:
        color = Qw.QColorDialog.getColor(
            self._color,
            self,
            self.dialog_title,
            Qw.QColorDialog.ShowAlphaChannel if self.use_alpha else 0,
        )
        if color.isValid() and color != self._color:
            self._color = color
            self.repaint()
            self.colorChanged.emit(color)

    def _draw_color(self, painter: Qg.QPainter) -> None:
        if self._color.alpha() != 255:
            self._draw_checkerboard(painter)
        painter.fillRect(0, 0, self.width(), self.height(), self._color)

    def _draw_checkerboard(self, painter: Qg.QPainter) -> None:
        for i in range(0, self.width(), 16):
            for j in range(0, self.height(), 16):
                if (i + j) % 32 == 0:
                    painter.fillRect(i, j, 16, 16, Qg.Qt.lightGray)
                else:
                    painter.fillRect(i, j, 16, 16, Qg.Qt.darkGray)

    def color(self) -> tuple[int, int, int, int]:
        return self._color.red(), self._color.green(), self._color.blue(), self._color.alpha()

    def setColor(self, color: tuple[int, int, int, int]) -> None:
        self._color = Qg.QColor(*color)
        self.repaint()
