"""
CLI handler for the ``render`` subcommand.

Draws the translated text from ``#translated.json`` sidecars onto cleaned page images
using the active workspace's render settings and fonts, writing ``<stem>_rendered.png``
per page.

Geometry comes from the translation sidecars; pass ``--scale`` if the translation boxes
are in a different resolution than the cleaned images.
"""

from pathlib import Path

import pcleaner.cli_utils as cli
import pcleaner.config as cfg
from pcleaner.workspace import Workspace
from pcleaner.translator import cache as tcache
from pcleaner.rendering.config import RenderConfig
from pcleaner.rendering.fonts import FontRegistry
from pcleaner.rendering import render as rnd


def _resolve_workspace_root(config: cfg.Config, workspace: str | None) -> Path | None:
    """Resolve the workspace root from a name/path option or the configured default."""
    target = workspace or config.default_workspace
    if target is None:
        return None
    as_path = Path(target)
    if Workspace.exists(as_path):
        return as_path
    match = cli.closest_match(target, list(config.saved_workspaces.keys()))
    if match is None:
        return None
    return config.saved_workspaces[match]


def _build_font_registry(ws: Workspace) -> FontRegistry:
    """Build a font registry from a workspace's render config, fonts map and fonts dir."""
    user_dirs = []
    fonts_dir = ws.root / "fonts"
    if fonts_dir.is_dir():
        user_dirs.append(fonts_dir)
    return FontRegistry(
        default_font=ws.render.default_font,
        per_language=ws.fonts,
        user_font_dirs=user_dirs,
    )


def _discover_images(image_paths: list[str]) -> list[Path]:
    """Expand the given files/directories into a flat list of image paths."""
    import pcleaner.helpers as hp

    images, _ = hp.discover_all_images(image_paths, cfg.SUPPORTED_IMG_TYPES)
    return images


def run_render(
    config: cfg.Config,
    image_paths: list[str],
    workspace: str | None,
    translations: str | None,
    output: str | None,
    scale: str | None,
) -> None:
    """
    Render translated text onto cleaned images.

    :param config: The global config.
    :param image_paths: Cleaned image files/directories to render onto.
    :param workspace: The workspace name or path (falls back to the default workspace).
    :param translations: Directory holding the ``#translated.json`` sidecars
        (default: the workspace cache directory).
    :param output: Output directory for rendered images (default: alongside each input).
    :param scale: Optional coordinate scale factor (string parsed to float, default 1.0).
    """
    root = _resolve_workspace_root(config, workspace)
    render_config = RenderConfig()
    fonts: FontRegistry
    translations_dir: Path | None = Path(translations) if translations else None

    if root is not None:
        try:
            ws = Workspace.load(root)
            render_config = ws.render
            fonts = _build_font_registry(ws)
            if translations_dir is None:
                translations_dir = ws.cache_dir()
        except FileNotFoundError:
            print(f"Workspace manifest missing at {root}.")
            return
    else:
        # No workspace: render with defaults and the bundled fallback font.
        fonts = FontRegistry(default_font=render_config.default_font)

    try:
        scale_factor = float(scale) if scale else 1.0
    except ValueError:
        print(f"Invalid --scale value: {scale}")
        return

    try:
        images = _discover_images(image_paths)
    except OSError as e:
        print(f"Error discovering images: {e}")
        return
    if not images:
        print("No images found to render.")
        return

    rendered = 0
    for image in images:
        sidecar_dir = translations_dir if translations_dir is not None else image.parent
        sidecar = tcache.sidecar_path(sidecar_dir, image)
        page_translation = tcache.load_if_exists(sidecar)
        if page_translation is None:
            print(f"  {image.name}: no translation sidecar at {sidecar.name}, skipping.")
            continue

        out_dir = Path(output) if output else image.parent
        out_path = out_dir / f"{image.stem}_rendered.png"
        rnd.render_to_file(image, page_translation, out_path, render_config, fonts, scale_factor)
        print(f"  {image.name}: {len(page_translation.results)} bubble(s) -> {out_path.name}")
        rendered += 1

    print(f"Rendered {rendered} image(s).")
