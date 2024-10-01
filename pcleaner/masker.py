from pathlib import Path
from typing import Sequence

from PIL import Image
from loguru import logger

import pcleaner.image_ops as ops
import pcleaner.structures as st
import pcleaner.output_structures as ost


def mask_page(m_data: st.MaskerData) -> Sequence[st.MaskFittingAnalytic]:
    """
    Do all the shit and return analytics for mask fitting.

    :param m_data: All the data needed for the cleaning process.
    :return: Analytics, consisting of the json file path, and a list of whether the mask was generated, the index of
        the best mask, and the border uniformity of the best mask for each box. This is a sequence because there is
        one for each bubble on the page.
    """

    page_data = st.PageData.from_json(m_data.json_path.read_text(encoding="utf-8"))

    # Make a shorter alias.
    m_conf = m_data.masker_config

    original_path = Path(page_data.original_path)
    path_gen = ost.OutputPathGenerator(original_path, m_data.cache_dir, m_data.json_path)

    def save_mask(img, path: Path) -> None:
        if m_data.show_masks:
            img.save(path)

    # Load the base image.
    base_image = Image.open(page_data.image_path)

    # Make a box mask. These will serve as basic masks as opposed to the AI generated precise ones.
    box_mask = page_data.make_box_mask(base_image.size, st.BoxType.EXTENDED_BOX)

    save_mask(box_mask, path_gen.box_mask)

    # Load the precise AI-generated mask.
    mask = Image.open(page_data.mask_path)
    mask = mask.convert("1", dither=Image.NONE)  # Convert to bitmap.

    # Cut the mask to the box mask, leaving only the intersection.
    cut_mask = ops.mask_intersection(mask, box_mask)

    save_mask(cut_mask, path_gen.cut_mask)

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
            analytics_page_path=Path(original_path),
        )
        for masking_box, reference_box in zip(
            page_data.merged_extended_boxes, page_data.reference_boxes
        )
    ]
    # Take out all entries that are None, since these masks were false positives.
    mask_fitments = [m for m in mask_fitments if m is not None]
    # Take out the analytics.
    # The analytics consist of (mask could be found: bool, mask index: int, border deviation: float)
    analytics: Sequence[st.MaskFittingAnalytic] = tuple(m.analytics for m in mask_fitments)

    # Remove entries if they failed.
    best_masks = [m for m in mask_fitments if not m.failed]

    combined_mask = ops.combine_best_masks(base_image.size, best_masks)

    if m_data.show_masks:
        # Save the masks in the debug folder.
        ops.visualize_mask_fitments(base_image, mask_fitments, path_gen.mask_fitments)

        # Output the result with the debug filter.
        combined_mask_debug = ops.apply_debug_filter_to_mask(combined_mask, m_conf.debug_mask_color)
        base_image_copy = base_image.copy()
        base_image_copy.paste(combined_mask_debug, (0, 0), combined_mask_debug)
        save_mask(base_image_copy, path_gen.with_masks)

        # Output diagnostics per box.
        ops.visualize_standard_deviations(base_image, mask_fitments, m_conf, path_gen.std_devs)

    # Save the combined mask for denoising.
    combined_mask.save(path_gen.combined_mask)
    save_denoising_data(
        Path(page_data.original_path),
        path_gen.combined_mask,
        Path(page_data.image_path),
        path_gen.mask_data_json,
        page_data.scale,
        mask_fitments,
    )

    # Carry on with creating the cleaned image.
    # If the scale isn't 1, then we need to reload the original image and scale the mask to fit.
    if page_data.scale != 1:
        cleaned_image = Image.open(page_data.original_path)
        combined_mask = combined_mask.resize(cleaned_image.size, Image.NEAREST)
    else:
        cleaned_image = base_image.copy()

    cleaned_image.paste(combined_mask, (0, 0), combined_mask)
    cleaned_image.save(path_gen.clean)

    if m_data.extract_text:
        # Extract the text layer from the image.
        logger.debug(f"Extracting text from {original_path}")
        original_image = Image.open(original_path)
        text_img = ops.extract_text(original_image, combined_mask)
        text_img.save(path_gen.text)

    return analytics


def save_denoising_data(
    original_path: Path,
    mask_path: Path,
    base_image_path: Path,
    json_output_path: Path,
    scale: float,
    mask_fitments: list[st.MaskFittingResults],
):
    """
    Save the data needed for denoising.

    :param original_path: The path to the original image.
    :param mask_path: The path to the combined mask.
    :param base_image_path: The path to the cached base image.
    :param json_output_path: The path to save to.
    :param scale: The scale of the original image to the cached base image.
    :param mask_fitments: The mask fitments.
    """

    # Gather the data needed for denoising, don't include those with a deviation greater than the max deviation.
    boxes_with_deviation = [
        (m.noise_mask_data[0], m.noise_mask_data[1], m.failed, m.analytics_thickness)
        for m in mask_fitments
    ]

    # Save the data.
    mask_data = st.MaskData(original_path, base_image_path, mask_path, scale, boxes_with_deviation)
    json_output_path.write_text(mask_data.to_json(), encoding="utf-8")
