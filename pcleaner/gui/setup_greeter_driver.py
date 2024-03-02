import PySide6.QtWidgets as Qw

import pcleaner.config as cfg
import pcleaner.model_downloader as md
from pcleaner.gui.ui_generated_files.ui_SetupGreeter import Ui_SetupGreeter


class SetupGreeter(Qw.QDialog, Ui_SetupGreeter):
    """
    A greeting dialog explaining that Panel Cleaner needs to download additional files before
    it can start. The user can then either proceed or abort.
    """

    def __init__(
        self,
        parent: Qw.QWidget | None = None,
        config: cfg.Config | None = None,
    ):
        """
        Initialize the widget.

        :param parent: The parent widget.
        """
        Qw.QDialog.__init__(self, parent)
        self.setupUi(self)

        # Update the placeholders.
        self.label_text_detector_path.setText(str(config.get_model_cache_dir()))
        self.label_ocr_path.setText(str(md.get_ocr_model_directory()))
        self.label_inpainting_path.setText(str(config.get_model_cache_dir()))
