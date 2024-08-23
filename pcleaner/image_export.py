from itertools import cycle
from pathlib import Path
from importlib import resources
from typing import Generator, Iterable, TypeVar, Any, NewType

import cv2
from attrs import frozen
import numpy as np
import colorsys
import scipy
from PIL import Image, ImageFilter, ImageDraw, ImageFont, ImageOps, ImageEnhance
from loguru import logger

import pcleaner.data
import pcleaner.config as cfg
import pcleaner.structures as st
import pcleaner.output_structures as ost

# SUPPORTED_IMG_TYPES = [".jpeg", ".jpg", ".png", ".bmp", ".tiff", ".tif", ".jp2", ".dib", ".webp", ".ppm"]

# Map the file extension to the type constant used in Pillow.
suffix_to_format: dict[str, str] = {
    ".jpg": "JPEG",
    ".jpeg": "JPEG",
    ".png": "PNG",
    ".webp": "WEBP",
    ".tiff": "TIFF",
    ".tif": "TIFF",
    ".bmp": "BMP",
    ".dib": "BMP",
    ".jp2": "JPEG2000",
    ".ppm": "PPM",
}


def save_optimized(
    image: Path | Image.Image, path: Path, original: Path | Image.Image | None = None
) -> None:
    """
    Save the image with optimized settings.

    :param image: The image to save.
    :param path: The path to save the image to, containing a suffix.
    :param original: The original image, used to determine the compression method, if applicable.
    """
    assert image is not None

    # Load the image if it's a path.
    if isinstance(image, Path):
        image = Image.open(image)

    compression_method = None
    original_image_mode = None
    original_dpi = None

    if original is not None:
        if isinstance(original, Path):
            original = Image.open(original)
        if suffix_to_format[path.suffix.lower()] == original.format:
            compression_method = original.info.get("compression", None)

        original_image_mode = original.mode
        original_dpi = original.info.get("dpi", None)

    if original_image_mode is not None:
        image = image.convert(original_image_mode)

    # Image args may be different depending on the image type.
    kwargs = {"optimize": True}

    match path.suffix.lower():
        case ".png":
            kwargs["compress_level"] = 9
        case ".jpg" | ".jpeg":
            kwargs["quality"] = 95
            kwargs["progressive"] = True
        case ".tif" | ".tiff":
            # Use tiff_lzw compression by default, rather than leaving them uncompressed.
            kwargs["compression"] = compression_method if compression_method else "tiff_lzw"

    if original_dpi is not None:
        kwargs["dpi"] = original_dpi
    logger.debug(f"Saving image {path.name} with kwargs: {kwargs}")
    image.save(path, **kwargs)


def copy_to_output_batched(arg_tuple: tuple) -> None:
    copy_to_output(*arg_tuple)


def copy_to_output(
    original_image_path: Path,
    cache_dir: Path,
    uuid_source: str | Path,
    outputs: list[ost.Output],
    output_directory: Path,
    preferred_file_type: str | None,
    preferred_mask_file_type: str,
    denoising_enabled: bool,
) -> None:
    """
    Copy or export the outputs from the cache directory to the output directory.
    Output paths and preferred file types are taken into account.

    Supported outputs:
    - Masked image: Output.masked_output
    - Final mask: Output.final_mask
    - Isolated text: Output.isolated_text
    - Denoised image: Output.denoised_output
    - Denoised Mask: Output.denoise_mask
    - Inpainted image: Output.inpainted_output
    - Inpainted Mask: Output.inpainted_mask

    This may raise OSError in various circumstances.

    We need to know if denoising was enabled so that we know to pull in the
    denoised mask when compositing the inpainting mask from the previous mask layers.

    :param original_image_path: The path to the original file to read it's metadata.
    :param cache_dir: Where the cached outputs are.
    :param uuid_source: One of the cached images with the uuid or the uuid itself.
    :param outputs: The outputs to copy.
    :param output_directory: The directory to write the outputs to.
    :param preferred_file_type: Profile setting.
    :param preferred_mask_file_type: Profile setting.
    :param denoising_enabled: Profile setting.
    """

    if output_directory.is_absolute():
        # When absolute, the output directory is used as is.
        final_out_path = output_directory / original_image_path.name
        path_gen = ost.OutputPathGenerator(original_image_path, output_directory, export_mode=True)
    else:
        # Otherwise, the output directory is relative to the original image's parent directory.
        final_out_path = original_image_path.parent / output_directory / original_image_path.name
        path_gen = ost.OutputPathGenerator(
            original_image_path, original_image_path.parent / output_directory, export_mode=True
        )

    final_out_path.parent.mkdir(parents=True, exist_ok=True)

    # Create png paths for the outputs.
    cleaned_out_path = path_gen.clean
    masked_out_path = path_gen.mask
    text_out_path = path_gen.text

    cache_path_gen = ost.OutputPathGenerator(original_image_path, cache_dir, uuid_source)

    # Check what the preferred output format is.
    if preferred_file_type is None:
        # Use the original file type by default.
        cleaned_out_path = cleaned_out_path.with_suffix(original_image_path.suffix)
    else:
        cleaned_out_path = cleaned_out_path.with_suffix(preferred_file_type)

    if preferred_mask_file_type is None:
        # Use png by default.
        masked_out_path = masked_out_path.with_suffix(".png")
        text_out_path = text_out_path.with_suffix(".png")
    else:
        masked_out_path = masked_out_path.with_suffix(preferred_mask_file_type)
        text_out_path = text_out_path.with_suffix(preferred_mask_file_type)

    # Preload the original image.
    original_image = Image.open(original_image_path)
    original_size = original_image.size

    # Output optimized images for all requested outputs.
    if ost.Output.masked_output in outputs:
        save_optimized(
            cache_path_gen.clean,
            cleaned_out_path,
            original_image,
        )

    if ost.Output.final_mask in outputs:
        # First scale the output mask to the original image size.
        final_mask = Image.open(cache_path_gen.combined_mask)
        final_mask = final_mask.resize(original_size, Image.NEAREST)
        save_optimized(final_mask, masked_out_path)

    if ost.Output.isolated_text in outputs:
        save_optimized(cache_path_gen.text, text_out_path)

    if ost.Output.denoised_output in outputs:
        save_optimized(
            cache_path_gen.clean_denoised,
            cleaned_out_path,
            original_image,
        )

    if ost.Output.denoise_mask in outputs:
        # Special case: Here we need to take the final mask, scale it up, and then paste this on top.
        final_mask = Image.open(cache_path_gen.combined_mask)
        final_mask = final_mask.resize(original_size, Image.BILINEAR)
        denoised_mask = Image.open(cache_path_gen.noise_mask)
        # Ensure both images are RGBA to safely alpha composite them.
        final_mask = final_mask.convert("RGBA")
        denoised_mask = denoised_mask.convert("RGBA")
        final_mask.alpha_composite(denoised_mask)

        save_optimized(final_mask, masked_out_path)

    if ost.Output.inpainted_output in outputs:
        save_optimized(
            cache_path_gen.clean_inpaint,
            cleaned_out_path,
            original_image,
        )

    if ost.Output.inpainted_mask in outputs:
        # Special case: Here we need to take the final mask, scale it up, and then paste the denoising
        final_mask = Image.open(cache_path_gen.combined_mask)
        final_mask = final_mask.resize(original_size, Image.NEAREST)
        final_mask = final_mask.convert("RGBA")

        if denoising_enabled:
            denoised_mask = Image.open(cache_path_gen.noise_mask)
            denoised_mask = denoised_mask.convert("RGBA")
            final_mask.alpha_composite(denoised_mask)

        inpainted_mask = Image.open(cache_path_gen.inpainting)
        inpainted_mask = inpainted_mask.convert("RGBA")
        final_mask.alpha_composite(inpainted_mask)

        save_optimized(final_mask, masked_out_path)


@frozen
class ExportTarget:
    original_path: Path
    uuid: str
    outputs: list[ost.Output]


def discover_viable_outputs(
    search_dir: Path,
    cleaned_outputs_whitelist: list[ost.Output],
    masked_outputs_whitelist: list[ost.Output],
    text_outputs_whitelist: list[ost.Output],
) -> list[ExportTarget]:
    """
    We need to export everything that is available for export, using the highest stage
    that isn't blocked by the profile and skip flags.
    Precedence: masker < denoiser < inpainter
    Viable candidates need at least a masked version, so the data is gathered from
    all available #clean.json files. Higher stage outputs are probed from there.



    :param search_dir: The cache directory to search in.
    :param cleaned_outputs_whitelist: Check for the highest output among these.
    :param masked_outputs_whitelist: Check for the highest output among these.
    :param text_outputs_whitelist: Check for the highest output among these.
    """
    export_targets = []

    json_files = list(Path(search_dir).glob("*#clean.json"))
    for file in json_files:
        page_data = st.PageData.from_json(file.read_text(encoding="utf-8"))

        cached_image_path = Path(page_data.image_path)
        path_gen = ost.OutputPathGenerator(
            Path(page_data.original_path), cached_image_path.parent, cached_image_path
        )

        # Iterate through all output types in descending order, starting with the highest
        # priority and checking if that file exists. Stop at the first one that exists, if any,
        # then moving on to the next category.
        target_outputs = []
        for out in cleaned_outputs_whitelist[::-1]:
            if path_gen.for_output(out).is_file():
                target_outputs.append(out)
                break
        for out in masked_outputs_whitelist[::-1]:
            if path_gen.for_output(out).is_file():
                target_outputs.append(out)
                break
        for out in text_outputs_whitelist[::-1]:
            if path_gen.for_output(out).is_file():
                target_outputs.append(out)
                break

        if target_outputs:
            logger.debug(
                f"Exporting image {path_gen.original_path.name} for outputs: {target_outputs}"
            )
        else:
            logger.debug(
                f"Skipping export of image {path_gen.original_path.name} due to no valid outputs being generated."
            )
            continue

        export_targets.append(ExportTarget(path_gen.original_path, path_gen.uuid, target_outputs))

    return export_targets