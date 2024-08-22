import PySide6.QtCore as Qc
import PySide6.QtGui as Qg
import PySide6.QtWidgets as Qw
from PySide6.QtCore import Slot


ICON_SCALE_FACTOR = 0.75  # Adjust as desired, where 1.0 means same as badge size


class BadgeButton(Qw.QPushButton):
    """
    This is a button with a badge in the top right corner.
    This can be shown or hidden at any time.
    As of now, the badge is the refresh icon on top of a colored circle using the
    highlight color of the palette.
    Additionally, you can set the button to replace the normal background color with
    the highlight color when the button is checked (as these are checkable buttons).
    That's called accented focus.
    I did this to make the checked-ness more obvious, due to most of the button being covered
    mostly by a pixmap, leaving only the edges visible.
    """

    badge_visible: bool
    badge_icon: Qg.QIcon
    accent_color: Qg.QColor
    can_uncheck: bool = False
    accented_focus: bool = True

    badge_size: int = 20
    badge_margin: int = 4

    def __init__(self, parent=None) -> None:
        Qw.QPushButton.__init__(self, parent=parent)
        self.badge_visible = False
        self.badge_icon = Qg.QIcon.fromTheme("view-refresh")
        # Get the accent color from the palette.
        self.update_accent_color()

        self.clicked.connect(self.handle_toggle)
        # self.toggled.connect(self.updateButtonPalette)

    @Qc.Slot(bool)
    def handle_toggle(self, checked: bool) -> None:
        """
        Check if the button can be unchecked, otherwise preventing such an action.

        :param checked: The new checked state.
        """
        if not self.can_uncheck and not checked:
            self.setChecked(True)

    def set_badge_size(self, size: int, margin: int) -> None:
        """
        Set the size of the badge and the margin around it.
        """
        self.badge_size = size
        self.badge_margin = margin

    def paintEvent(self, event) -> None:
        # Let QPushButton handle its default painting.
        Qw.QPushButton.paintEvent(self, event)

        painter = Qg.QPainter(self)

        if self.isChecked() and self.accented_focus and self.icon():
            # Draw a slight accent color overlay over the pixmap displayed on the button.
            transparent_accent = Qg.QColor(self.accent_color)
            transparent_accent.setAlpha(50)
            painter.setBrush(transparent_accent)
            painter.setPen(Qc.Qt.NoPen)
            # Get rect of the pixmap.
            pixmap_rect = Qc.QRect(0, 0, self.iconSize().width(), self.iconSize().height())
            pixmap_rect.moveCenter(self.rect().center())
            painter.drawRect(pixmap_rect)

        if self.badge_visible:
            # Draw the badge in the top right corner, with a margin.
            badge_rect = Qc.QRect(
                self.width() - self.badge_size - self.badge_margin,
                self.badge_margin,
                self.badge_size,
                self.badge_size,
            )

            # Draw a dropshadow for the badge.
            painter.setBrush(Qg.QColor(0, 0, 0, 80))
            painter.setPen(Qc.Qt.NoPen)
            painter.drawEllipse(badge_rect.translated(2, 2))

            # Draw the colored circle background for the badge, including a dark border.
            darker_accent = self.accent_color.darker(150)
            painter.setBrush(darker_accent)
            painter.setPen(Qc.Qt.NoPen)
            painter.drawEllipse(badge_rect + Qc.QMargins(1, 1, 1, 1))
            painter.setBrush(self.accent_color)
            painter.drawEllipse(badge_rect)

            # Calculate the size of the smaller icon rectangle.
            icon_size = int(self.badge_size * ICON_SCALE_FACTOR)
            pixmap = self.badge_icon.pixmap(Qc.QSize(icon_size, icon_size))

            # Calculate the top-left point for drawing the pixmap to center it.
            pixmap_x = badge_rect.center().x() - icon_size // 2
            pixmap_y = badge_rect.center().y() - icon_size // 2
            # Draw the centered icon pixmap.
            # Fuck this shit I'm hard-coding a 1px offset, no bloody clue why it's off by one otherwise.
            painter.drawPixmap(pixmap_x + 1, pixmap_y + 1, pixmap)

    def changeEvent(self, event: Qc.QEvent) -> None:
        super(BadgeButton, self).changeEvent(event)
        if event.type() == Qc.QEvent.PaletteChange:
            self.update_accent_color()
            self.update()

    @Slot(bool)
    def updateButtonPalette(self, checked) -> None:
        palette = self.palette()
        if checked:  # and self.accented_focus:
            palette.setColor(Qg.QPalette.Button, self.accent_color)
        else:
            # Reset to the default button color
            palette.setColor(
                Qg.QPalette.Button, palette.color(Qg.QPalette.Normal, Qg.QPalette.Button)
            )
        self.setPalette(palette)

    def update_accent_color(self) -> None:
        """
        Use the Highlight color, aka Accent color to draw the background of the badge.
        """
        self.accent_color = self.palette().color(Qg.QPalette.ColorRole.Highlight)
        if self.accented_focus:
            self.setStyleSheet(
                """
                QPushButton:checked {
                    background-color: palette(highlight);
                }
                """
            )

    def set_badge_visible(self, visible: bool) -> None:
        self.badge_visible = visible
        self.update()

    def hide_badge(self) -> None:
        self.set_badge_visible(False)

    def show_badge(self) -> None:
        self.set_badge_visible(True)
