from pathlib import Path

from PIL import Image
from logzero import logger

import pcleaner.image_ops as ops
import pcleaner.structures as st


def clean_page(c_data: st.CleanerData) -> list[tuple[Path, bool, int, float]]:
    """
    Do all the shit and return analytics for mask fitting.

    :param c_data: All the data needed for the cleaning process.
    :return: Analytics, consisting of the json file path, and a list of whether the mask was generated, the index of
        the best mask, and the border uniformity of the best mask for each box.
    """

    page_data = st.PageData.from_json(c_data.json_path.read_text())

    # Make a shorter alias.
    cleaner_conf = c_data.cleaner_config

    original_img_path_as_png = Path(page_data.original_path).with_suffix(
        ".png"
    )  # Make sure all derived file names are .png.
    cache_out_path = c_data.cache_dir / original_img_path_as_png.name
    logger.debug(f"Masking {cache_out_path.name}...")

    def save_mask(img, name_suffix):
        if c_data.show_masks:
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
            cleaner_conf=cleaner_conf,
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

    if c_data.show_masks:
        # Save the masks in the debug folder.
        ops.visualize_mask_fitments(
            base_image, mask_fitments, cache_out_path.with_stem(cache_out_path.stem + "_masks")
        )

        # Output the result with the debug filter.
        combined_mask_debug = ops.apply_debug_filter_to_mask(
            combined_mask, cleaner_conf.debug_mask_color
        )
        base_image_copy = base_image.copy()
        base_image_copy.paste(combined_mask_debug, (0, 0), combined_mask_debug)
        save_mask(base_image_copy, "_with_masks")

    base_image.paste(combined_mask, (0, 0), combined_mask)

    # Save the combined mask. This will be used for denoising.
    combined_mask_path = cache_out_path.with_stem(cache_out_path.stem + "_combined_mask")
    combined_mask.save(combined_mask_path)
    cleaned_image_path = cache_out_path.with_stem(cache_out_path.stem + "_cleaned")
    base_image.save(cleaned_image_path)
    save_denoising_data(
        original_img_path_as_png,
        cleaned_image_path,
        combined_mask_path,
        cache_out_path,
        mask_fitments,
    )

    # Settle on the final output path for the cleaned image.
    # Check if outputting directly.
    if c_data.output_dir is not None:
        if c_data.output_dir.is_absolute():
            final_out_path = c_data.output_dir / original_img_path_as_png.name
        else:
            # Take the original image path, and place the image in a subdirectory.
            # This is for when multiple directories were passed in.
            final_out_path = (
                original_img_path_as_png.parent / c_data.output_dir / original_img_path_as_png.name
            )

        final_out_path.parent.mkdir(parents=True, exist_ok=True)
        final_cleaned_out_path = final_out_path.with_name(final_out_path.stem + "_clean.png")
        final_mask_out_path = final_out_path.with_name(final_out_path.stem + "_mask.png")

        logger.debug(f"Final output path: {final_cleaned_out_path}")

        # The arg parser should ensure that both can't be true at once, not like that'd be an issue, just plain silly.
        if not c_data.save_only_mask:
            # Save the final image.
            logger.debug(f"Saving final image to {final_cleaned_out_path}")
            base_image.save(final_cleaned_out_path)

        if not c_data.save_only_cleaned:
            # Save the final image.
            logger.debug(f"Saving final mask to {final_mask_out_path}")
            combined_mask.save(final_mask_out_path)

    return analytics


def save_denoising_data(
    original_img_path: Path,
    cleaned_path: Path,
    mask_path: Path,
    cache_path: Path,
    mask_fitments: list[st.MaskFittingResults],
):
    """
    Save the data needed for denoising.

    Gather the following to construct a MaskData struct:
    - original_path: Path
    - cleaned_path: Path
    - mask_path: Path
    - boxes_with_deviation: list[tuple[tuple[int, int, int, int], float]]

    :param original_img_path: The path to the original image.
    :param cleaned_path: The path to the cleaned image.
    :param mask_path: The path to the combined mask.
    :param cache_path: The path to the cache directory.
    :param mask_fitments: The mask fitments.
    """

    # Gather the data needed for denoising.
    boxes_with_deviation = [m.noise_mask_data for m in mask_fitments]

    # Save the data.
    mask_data = st.MaskData(original_img_path, cleaned_path, mask_path, boxes_with_deviation)
    mask_data.write_json(cache_path.with_name(cache_path.stem + "_mask_data.json"))
