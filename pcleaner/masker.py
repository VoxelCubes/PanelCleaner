from pathlib import Path

from PIL import Image
from logzero import logger, loglevel, DEBUG, INFO

import pcleaner.image_ops as ops
import pcleaner.structures as st


def clean_page(m_data: st.MaskerData) -> list[tuple[Path, bool, int, float]]:
    """
    Do all the shit and return analytics for mask fitting.

    :param m_data: All the data needed for the cleaning process.
    :return: Analytics, consisting of the json file path, and a list of whether the mask was generated, the index of
        the best mask, and the border uniformity of the best mask for each box.
    """

    page_data = st.PageData.from_json(m_data.json_path.read_text())

    # Make a shorter alias.
    g_conf = m_data.general_config
    m_conf = m_data.masker_config

    original_path = Path(page_data.original_path)
    original_img_path_as_png = original_path.with_suffix(
        ".png"
    )  # Make sure all derived file names are .png.
    # Clobber protection prefixes have the form "[A-Z]{4}-\d+_file name", ex. JMCF-0_0023.json
    clobber_protection_prefix = m_data.json_path.stem.split("_")[0]
    cache_out_path = (
        m_data.cache_dir / f"{clobber_protection_prefix}_{original_img_path_as_png.name}"
    )

    def save_mask(img, name_suffix):
        if m_data.show_masks:
            img.save(cache_out_path.with_stem(cache_out_path.stem + name_suffix))

    # Load the base image.
    base_image = Image.open(page_data.image_path)

    # Make a box mask. These will serve as basic masks as opposed to the AI generated precise ones.
    box_mask = page_data.make_box_mask(base_image.size, st.BoxType.EXTENDED_BOX)

    save_mask(box_mask, "_box_mask")

    # Load the precise AI-generated mask.
    mask = Image.open(page_data.mask_path)
    mask = mask.convert("1", dither=Image.NONE)  # Convert to bitmap.

    # Cut the mask to the box mask, leaving only the intersection.
    cut_mask = ops.mask_intersection(mask, box_mask)

    save_mask(cut_mask, "_cut_mask")

    # Use the merged extended boxes to guard against overlapping boxes after having extended them.
    # Generate varying sizes of the precise mask and then rank them based on border uniformity.
    mask_fitments: list[st.MaskFittingResults] = [
        ops.pick_best_mask(
            base=base_image,
            precise_mask=cut_mask,
            box_mask=box_mask,
            masking_box=masking_box,
            reference_box=reference_box,
            masker_conf=m_conf,
            scale=page_data.scale,
            save_masks=m_data.show_masks,
            analytics_page_path=Path(original_img_path_as_png),
        )
        for masking_box, reference_box in zip(
            page_data.merged_extended_boxes, page_data.reference_boxes
        )
    ]
    # Take out all entries that are None, since these masks were false positives.
    mask_fitments = [m for m in mask_fitments if m is not None]
    # Take out the analytics.
    # The analytics consist of (mask could be found: bool, mask index: int, border deviation: float)
    analytics: list[tuple[Path, bool, int, float]] = [m.analytics for m in mask_fitments]

    # Remove entries if they failed.
    best_masks = [m for m in mask_fitments if not m.failed]

    combined_mask = ops.combine_best_masks(base_image.size, best_masks)

    if m_data.show_masks:
        # Save the masks in the debug folder.
        ops.visualize_mask_fitments(
            base_image, mask_fitments, cache_out_path.with_stem(cache_out_path.stem + "_masks")
        )

        # Output the result with the debug filter.
        combined_mask_debug = ops.apply_debug_filter_to_mask(combined_mask, m_conf.debug_mask_color)
        base_image_copy = base_image.copy()
        base_image_copy.paste(combined_mask_debug, (0, 0), combined_mask_debug)
        save_mask(base_image_copy, "_with_masks")

    # Save the combined mask for denoising.
    combined_mask_path = cache_out_path.with_stem(cache_out_path.stem + "_combined_mask")
    combined_mask.save(combined_mask_path)
    save_denoising_data(
        Path(page_data.original_path),
        original_img_path_as_png,
        combined_mask_path,
        Path(page_data.image_path),
        cache_out_path,
        page_data.scale,
        m_conf.mask_max_standard_deviation,
        mask_fitments,
    )

    # Settle on the final output path for the cleaned image.
    # Check if outputting directly.
    if m_data.output_dir is not None:
        # If the scale isn't 1, then we need to reload the original image and scale the mask to fit.
        if page_data.scale != 1:
            cleaned_image = Image.open(page_data.original_path)
            combined_mask = combined_mask.resize(cleaned_image.size, Image.NEAREST)
        else:
            cleaned_image = base_image.copy()

        cleaned_image.paste(combined_mask, (0, 0), combined_mask)

        if m_data.output_dir.is_absolute():
            final_out_path = m_data.output_dir / original_img_path_as_png.name
        else:
            # Take the original image path, and place the image in a subdirectory.
            # This is for when multiple directories were passed in.
            final_out_path = (
                original_img_path_as_png.parent / m_data.output_dir / original_img_path_as_png.name
            )

        final_out_path.parent.mkdir(parents=True, exist_ok=True)
        final_cleaned_out_path = final_out_path.with_name(final_out_path.stem + "_clean.png")
        final_mask_out_path = final_out_path.with_name(final_out_path.stem + "_mask.png")

        # Check what the preferred output format is.
        if g_conf.preferred_file_type is None:
            # Use the original file type.
            final_cleaned_out_path = final_cleaned_out_path.with_suffix(
                Path(page_data.original_path).suffix
            )
        else:
            final_cleaned_out_path = final_cleaned_out_path.with_suffix(g_conf.preferred_file_type)

        if g_conf.preferred_mask_file_type is None:
            # Use png by default.
            final_mask_out_path = final_mask_out_path.with_suffix(".png")
        else:
            final_mask_out_path = final_mask_out_path.with_suffix(g_conf.preferred_mask_file_type)

        # The arg parser should ensure that both can't be true at once, not like that'd be an issue, just plain silly.
        if not m_data.save_only_mask and not m_data.save_only_text:
            # Save the final image.
            logger.debug(f"Saving final image to {final_cleaned_out_path}")
            ops.save_optimized(cleaned_image, final_cleaned_out_path, original_path)

        if not m_data.save_only_cleaned and not m_data.save_only_text:
            # Save the final image.
            logger.debug(f"Saving final mask to {final_mask_out_path}")
            ops.save_optimized(combined_mask, final_mask_out_path)

        if m_data.extract_text:
            # Extract the text layer from the image.
            logger.debug(f"Extracting text from {final_cleaned_out_path}")
            text_img = ops.extract_text(base_image, combined_mask)
            text_out_path = final_out_path.with_name(final_out_path.stem + "_text.png")
            if g_conf.preferred_mask_file_type is None:
                # Use png by default.
                text_out_path = text_out_path.with_suffix(".png")
            else:
                text_out_path = text_out_path.with_suffix(g_conf.preferred_mask_file_type)
            ops.save_optimized(text_img, text_out_path, original_path)

    return analytics


def save_denoising_data(
    original_path: Path,
    target_path: Path,
    mask_path: Path,
    base_image_path: Path,
    cache_path: Path,
    scale: float,
    mask_max_deviation: float,
    mask_fitments: list[st.MaskFittingResults],
):
    """
    Save the data needed for denoising.

    :param original_path: The path to the original image.
    :param target_path: The path to the original image with png suffix.
    :param mask_path: The path to the combined mask.
    :param base_image_path: The path to the cached base image.
    :param cache_path: The path to the cache directory.
    :param scale: The scale of the original image to the cached base image.
    :param mask_max_deviation: The maximum deviation of the mask.
    :param mask_fitments: The mask fitments.
    """

    # Gather the data needed for denoising, don't include those with a deviation greater than the max deviation.
    boxes_with_deviation = [
        m.noise_mask_data for m in mask_fitments if m.analytics_std_deviation <= mask_max_deviation
    ]

    # Save the data.
    mask_data = st.MaskData(
        original_path, target_path, base_image_path, mask_path, scale, boxes_with_deviation
    )
    mask_data.write_json(cache_path.with_name(cache_path.stem + "#mask_data.json"))
