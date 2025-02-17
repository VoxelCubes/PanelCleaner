import sys
import platform
import subprocess
from importlib import resources
from enum import Enum, auto
from pathlib import Path

import PySide6.QtWidgets as Qw
import xdg
from loguru import logger

import pcleaner.gui.gui_utils as gu
import pcleaner.data
import pcleaner.helpers as hp
from pcleaner.gui.ui_generated_files.ui_FileManagerIntegration import Ui_FileManagerExtension


class ExtensionTarget(Enum):
    Unsupported = auto()
    Dolphin = auto()
    WindowsExplorer = auto()


def get_extension_target() -> ExtensionTarget:
    """
    Get the file manager extension target.
    """
    if platform.system() == "Linux":
        # Make sure this isn't the flatpak version:
        if Path("/.flatpak-info").exists():
            return ExtensionTarget.Unsupported
        # Check which file manager is installed:
        try:
            subprocess.run(["which", "dolphin"], check=True)
            return ExtensionTarget.Dolphin
        except subprocess.CalledProcessError:
            return ExtensionTarget.Unsupported
    elif platform.system() == "Windows":
        # I've had it, fuck this. Someone else can try again.
        return ExtensionTarget.Unsupported
        # I dunno how to make this work well with the bare script version, so only exe supported.
        if getattr(sys, "frozen", False):
            return ExtensionTarget.WindowsExplorer
        else:
            return ExtensionTarget.Unsupported
    else:
        return ExtensionTarget.Unsupported


def get_plasma_service_menu_path() -> Path:
    """
    Get the default path, accounting for XDG.
    ~/.local/share/kio/servicemenus/panelcleaner.desktop

    :return: The path to store the service menu file as.
    """
    return Path(xdg.XDG_DATA_HOME) / "kio" / "servicemenus" / "panelcleaner.desktop"


class FileManagerExtension(Qw.QDialog, Ui_FileManagerExtension):
    """
    Allow the user to add or remove a file manager extension, if system is supported.
    """

    def __init__(
        self,
        parent=None,
    ) -> None:
        """
        Init the widget.

        :param parent: The parent widget.
        """
        Qw.QDialog.__init__(self, parent)
        self.setupUi(self)

        self.commandLinkButton_install.clicked.connect(self.install_extension)

        self.commandLinkButton_uninstall.clicked.connect(self.uninstall_extension)

        target = get_extension_target()
        if target == ExtensionTarget.Unsupported:
            gu.show_warning(
                self, self.tr("Unsupported system"), self.tr("This system is not supported.")
            )
            self.close()
        elif target == ExtensionTarget.Dolphin:
            self.commandLinkButton_install.setText(self.tr("Install for Dolphin"))
            self.commandLinkButton_uninstall.setText(self.tr("Uninstall for Dolphin"))
            self.commandLinkButton_install.setDescription(
                self.tr(
                    "The extension will be installed at {path}. "
                    "This doesn't require root permissions.".format(
                        path=get_plasma_service_menu_path()
                    )
                )
            )
            self.commandLinkButton_uninstall.setDescription(
                self.tr(
                    "The extension file will be deleted. This doesn't require root permissions."
                )
            )
        elif target == ExtensionTarget.WindowsExplorer:
            self.commandLinkButton_install.setText(self.tr("Install for Windows Explorer"))
            self.commandLinkButton_uninstall.setText(self.tr("Uninstall for Windows Explorer"))
            self.commandLinkButton_install.setDescription(
                self.tr(
                    "The extension will be installed in the Windows registry."
                    "This requires admin permissions."
                )
            )
            self.commandLinkButton_uninstall.setDescription(
                self.tr(
                    "The extension will be uninstalled from the Windows registry."
                    "This requires admin permissions."
                )
            )

    def install_extension(self) -> None:
        """
        Install the file manager extension.
        """
        target = get_extension_target()
        if target == ExtensionTarget.Unsupported:
            # This dialog shouldn't appear if the system is unsupported anyway.
            raise NotImplementedError("Unsupported system.")

        if target == ExtensionTarget.Dolphin:
            self.install_for_dolphin()
        elif target == ExtensionTarget.WindowsExplorer:
            self.install_for_windows_explorer()

    def uninstall_extension(self) -> None:
        """
        Uninstall the file manager extension.
        """
        target = get_extension_target()
        if target == ExtensionTarget.Unsupported:
            # This dialog shouldn't appear if the system is unsupported anyway.
            raise NotImplementedError("Unsupported system.")

        if target == ExtensionTarget.Dolphin:
            self.uninstall_for_dolphin()
        elif target == ExtensionTarget.WindowsExplorer:
            self.uninstall_for_windows_explorer()

    # ============================================== Install ==============================================

    def install_for_dolphin(self) -> None:
        """
        Install the file manager extension for Dolphin.
        """
        try:
            desktop_file_contents = format_desktop_entry()
            target_path = get_plasma_service_menu_path()

            msg = self.tr("Dolphin extension installed successfully.")
            if not target_path.parent.is_dir():
                msg = self.tr(
                    "Dolphin extension installed successfully.\n"
                    "You may need to log out and log back in (or restart) for the changes to take effect."
                )
            target_path.parent.mkdir(parents=True, exist_ok=True)

            if target_path.exists():
                target_path.unlink()

            target_path.write_text(desktop_file_contents)
            target_path.chmod(0o755)  # rwx r-x r-x Make it executable.
            gu.show_info(
                self,
                self.tr("Installation successful"),
                msg,
            )
        except Exception:
            gu.show_exception(
                self,
                self.tr("Installation failed"),
                self.tr("Failed to install Dolphin extension."),
            )

    def install_for_windows_explorer(self) -> None:
        """
        Install the file manager extension for Windows Explorer.
        """
        try:
            target_path = get_pcleaner_path()
            if target_path is None:
                logger.error("Can't determine where to point the windows explorer integration.")
                return
            logger.info(f"Pointing windows explorer integration to {target_path}")
            execution: list[Path | str] = get_executable_target()
            execution.extend(["create", target_path])
            logger.info(f"Executing subprocess: {execution}")
            subprocess.check_output(execution)
            gu.show_info(
                self, "Installation Success", "Successfully installed the Explorer integration."
            )
        except Exception:
            gu.show_exception(
                self,
                self.tr("Installation failed"),
                self.tr("Failed to install Windows Explorer extension."),
            )

    # ============================================== Uninstall ==============================================

    def uninstall_for_dolphin(self) -> None:
        """
        Uninstall the file manager extension for Dolphin.
        """
        try:
            target_path = get_plasma_service_menu_path()
            if target_path.exists():
                target_path.unlink()
                gu.show_info(
                    self,
                    self.tr("Uninstallation successful"),
                    self.tr("Dolphin extension uninstalled successfully."),
                )
            else:
                gu.show_info(
                    self,
                    self.tr("Uninstallation successful"),
                    self.tr("Dolphin extension was not installed."),
                )
        except Exception:
            gu.show_exception(
                self,
                self.tr("Uninstallation failed"),
                self.tr("Failed to uninstall Dolphin extension."),
            )

    def uninstall_for_windows_explorer(self) -> None:
        """
        Uninstall the file manager extension for Windows Explorer.
        """
        try:
            execution: list[Path | str] = get_executable_target()
            execution.extend(["delete", ""])
            logger.info(f"Executing subprocess: {execution}")
            subprocess.check_output(execution)
            gu.show_info(
                self, "Uninstallation Success", "Successfully uninstalled the Explorer integration."
            )
        except Exception:
            gu.show_exception(
                self,
                self.tr("Uninstallation failed"),
                self.tr("Failed to uninstall Windows Explorer extension."),
            )


def format_desktop_entry() -> str:
    """
    Format the desktop entry for the file manager extension.
    """
    return f"""\
[Desktop Entry]
Type=Service
MimeType=image/*;inode/directory;
Actions=cleanBoth;onlyMask;onlyClean;
X-KDE-Submenu=Panel Cleaner...


[Desktop Action cleanBoth]
Name=Save both the cleaned image and mask
Icon=background
Exec=pcleaner clean --notify %u
Icon=panelcleaner

[Desktop Action onlyMask]
Name=Save only the mask
Icon=background
Exec=pcleaner clean --notify -m %u
Icon=panelcleaner

[Desktop Action onlyClean]
Name=Save only the cleaned image
Icon=background
Exec=pcleaner clean --notify -c %u
Icon=panelcleaner

"""


def get_executable_target() -> list[Path]:
    """
    For a regular script, we want to return
    "path to python executable", "path to regedit script"

    But for the pyinstaller bundle, we can't use the bundled interpreter,
    so we need to instead point to the pre-built exe that bundles those two together.

    :return: execution path(s)
    """
    if getattr(sys, "frozen", False):
        # We need to fall back to the bundle.
        return [hp.resource_path(pcleaner.data, "WindowsExplorerIntegrationRegedit.exe")]

    else:
        python_interpreter = Path(sys.executable)
        return [
            python_interpreter,
            hp.resource_path(pcleaner.data, "windows_explorer_integration_regedit.py"),
        ]


def get_pcleaner_path() -> Path | None:
    # determine if application is a script file or frozen exe.
    if getattr(sys, "frozen", False):
        return Path(sys.executable)
    elif __file__:
        return Path(__file__).parent.parent / "main.py"
    return None
