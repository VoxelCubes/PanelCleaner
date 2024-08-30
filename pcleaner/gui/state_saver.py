import PySide6.QtCore as Qc
import PySide6.QtWidgets as Qw
from loguru import logger


class StateSaver:
    """
    A class to save and restore the state of various widgets
    using the QSettings API.
    """

    widgets: set[Qw.QWidget]
    settings: Qc.QSettings
    name: str  # The namespace in the settings file.
    no_save: bool

    def __init__(self, name: str) -> None:
        self.name = name
        self.widgets = set()
        self.settings = Qc.QSettings("pcleaner", "window_state")
        self.no_save = False

    def register(self, *widget: Qw.QWidget):
        """
        Register a widget to be saved and restored.
        """
        self.widgets.update(widget)

    def save(self):
        """
        Save the state of all registered widgets.
        """
        if self.no_save:
            return

        self.settings.beginGroup(self.name)
        try:
            for widget in self.widgets:
                if isinstance(widget, Qw.QSplitter):
                    self.settings.setValue(widget.objectName(), widget.saveState())
                elif isinstance(widget, Qw.QCheckBox):
                    self.settings.setValue(widget.objectName(), widget.isChecked())
                elif isinstance(widget, Qw.QRadioButton):
                    self.settings.setValue(widget.objectName(), widget.isChecked())
                elif isinstance(widget, Qw.QLineEdit):
                    self.settings.setValue(widget.objectName(), widget.text())
                elif isinstance(widget, Qw.QComboBox):
                    self.settings.setValue(widget.objectName(), widget.currentIndex())
                elif isinstance(widget, Qw.QSpinBox):
                    self.settings.setValue(widget.objectName(), widget.value())
                elif isinstance(widget, Qw.QTableWidget):
                    self.settings.setValue(
                        widget.objectName(), widget.horizontalHeader().saveState()
                    )
                elif isinstance(widget, Qw.QAbstractSlider):
                    self.settings.setValue(widget.objectName(), widget.value())
                elif isinstance(widget, Qw.QWidget):
                    self.settings.setValue(widget.objectName(), widget.saveGeometry())
                else:
                    logger.warning(f"Unknown widget type: {widget}")
        except Exception as e:
            logger.error(f"Failed to save widget state: {e} for {self.name}")
        finally:
            self.settings.endGroup()
        logger.debug(f"Saved state for {self.name}")

    # noinspection PyTypeChecker
    def restore(self):
        """
        Restore the state of all registered widgets.
        """
        self.settings.beginGroup(self.name)
        try:
            for widget in self.widgets:
                # Skip if there is nothing to load.
                if not self.settings.contains(widget.objectName()):
                    continue
                if isinstance(widget, Qw.QSplitter):
                    widget.restoreState(self.settings.value(widget.objectName()))
                elif isinstance(widget, Qw.QCheckBox):
                    value = self.settings.value(widget.objectName())
                    widget.setChecked(value == "true")
                elif isinstance(widget, Qw.QRadioButton):
                    value = self.settings.value(widget.objectName())
                    widget.setChecked(value == "true")
                    if value == "true":
                        widget.clicked.emit()
                elif isinstance(widget, Qw.QLineEdit):
                    widget.setText(self.settings.value(widget.objectName()))
                elif isinstance(widget, Qw.QComboBox):
                    widget.setCurrentIndex(int(self.settings.value(widget.objectName())))
                elif isinstance(widget, Qw.QSpinBox):
                    widget.setValue(int(self.settings.value(widget.objectName())))
                elif isinstance(widget, Qw.QTableWidget):
                    widget.horizontalHeader().restoreState(self.settings.value(widget.objectName()))
                elif isinstance(widget, Qw.QAbstractSlider):
                    widget.setValue(int(self.settings.value(widget.objectName())))
                elif isinstance(widget, Qw.QWidget):
                    widget.restoreGeometry(self.settings.value(widget.objectName()))
                else:
                    logger.warning(f"Unknown widget type: {widget}")
        except Exception as e:
            logger.error(f"Failed to restore widget state: {e} for {self.name}")
        finally:
            self.settings.endGroup()
        logger.debug(f"Restored state for {self.name}")

    def delete_all(self):
        """
        Delete all saved settings.
        """
        self.settings.clear()
        self.no_save = True
        logger.debug(f"Deleted all saved settings for {self.name}")
