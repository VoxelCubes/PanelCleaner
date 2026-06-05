"""
Standalone launcher for the Webtoon Translate & Cleaner GUI tools.

Opens the workspace browser (and, from there, the glossary editor) without requiring the
full main window. This keeps the new GUI usable and decoupled while the deeper main-window
integration is done separately. Invoked by ``pcleaner workspace gui``.
"""

import sys

from loguru import logger

import pcleaner.config as cfg


def launch(config: cfg.Config, workspace: str | None = None) -> int:
    """
    Show the workspace browser dialog, creating a QApplication if needed.

    :param config: The loaded global config.
    :param workspace: Optional workspace name to open the glossary editor for directly.
    :return: The dialog exit code.
    """
    import PySide6.QtWidgets as Qw

    from pcleaner.gui.workspace_browser import WorkspaceBrowser

    app = Qw.QApplication.instance()
    owns_app = app is None
    if owns_app:
        app = Qw.QApplication(sys.argv)

    browser = WorkspaceBrowser(config)

    # If a workspace was named, jump straight into its glossary editor on top of the browser.
    if workspace is not None:
        _open_glossary_for(config, workspace, browser)

    result = browser.exec()
    logger.debug(f"Workspace browser closed with code {result}.")
    return result


def _open_glossary_for(config: cfg.Config, workspace: str, parent) -> None:
    import pcleaner.cli_utils as cli
    from pcleaner.workspace import Workspace
    from pcleaner.gui.glossary_editor import GlossaryEditor

    target = workspace
    if not Workspace.exists(target):
        match = cli.closest_match(workspace, list(config.saved_workspaces.keys()))
        if match is None:
            return
        target = config.saved_workspaces[match]
    try:
        ws = Workspace.load(target)
    except FileNotFoundError:
        return
    GlossaryEditor.edit_path(ws.resolve_glossary_path(), parent).exec()
