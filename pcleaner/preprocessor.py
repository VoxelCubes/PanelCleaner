import json
import re
from copy import copy
from pathlib import Path

from PIL import Image
from loguru import logger
from manga_ocr import MangaOcr

import pcleaner.config as cfg
import pcleaner.ctd_interface as ctm
import pcleaner.structures as st


def generate_mask_data(
    image_path: list[Path],
    config_general: cfg.GeneralConfig,
    config_detector: cfg.TextDetectorConfig,
    model_path: Path,
    output_dir: Path,
) -> None:
    """
    Run the ai model to generate masks and box data for the given image,
    or all images in the given directory.

    :param image_path: Path to the image or directory of images.
    :param config_general: General configuration, part of the profile.
    :param config_detector: Text detector configuration, part of the profile.
    :param model_path: Path to the model file.
    :param output_dir: Path to the directory where the results will be saved.
    """

    ctm.model2annotations(config_general, config_detector, model_path, image_path, output_dir)


def prep_json_file(
    json_file_path: Path,
    preprocessor_conf: cfg.PreprocessorConfig,
    cache_masks: bool,
    mocr: MangaOcr | None = None,
    cache_masks_ocr: bool = False,
    performing_ocr: bool = False,
) -> st.OCRAnalytic | None:
    """
    Load the generated json file, and clean the data, leaving only the
    relevant data for the following steps.

    Check that this file wasn't already processed, and if it was, skip it.
    Processed json files have the file name ending with '#clean.json'.

    If a manga ocr object is given, run ocr on small boxes to determine whether
    they contain mere symbols, in which case these boxes do not need to be cleaned
    and can be removed from the dataset.
    The model must be initialized somewhere else to lessen coupling, and to avoid the long
    initialization time for each page.

    Performing OCR means that the output is not for cleaning, therefore we can immediately discard any
    boxes that cannot be processed by the OCR model, which has limited language support.

    :param json_file_path: Path to the json file.
    :param preprocessor_conf: Preprocessor configuration, part of the profile.
    :param cache_masks: Whether to cache the masks.
    :param mocr: [Optional] Manga ocr object.
    :param cache_masks_ocr: [Optional] Whether to cache the masks early for ocr.
    :param performing_ocr: [Optional] Whether the actual output is for ocr, not cleaning.
    :return: Analytics data if the manga ocr object is given, None otherwise.
    """
    logger.debug(f"Processing json file: {json_file_path}")

    # Check if the file was already processed.
    if not json_file_path.name.endswith("#raw.json"):
        return None

    json_data = json.loads(json_file_path.read_text(encoding="utf-8"))

    image_path: str = json_data["image_path"]
    mask_path: str = json_data["mask_path"]
    original_path: str = json_data["original_path"]
    scale: float = json_data["scale"]
    boxes: list[st.Box] = []

    # Define permitted languages based on strictness.
    # Since the OCR model is only trained to recognize Japanese,
    # we need to discard anything that isn't, and if strict, also
    # those that are unknown (likely a mix).
    language_whitelist = ["ja"]
    if not preprocessor_conf.ocr_strict_language:
        language_whitelist.append("unknown")

    for data in json_data["blk_list"]:
        # Check box language.
        if performing_ocr and data["language"] not in language_whitelist:
            continue

        box = st.Box(*data["xyxy"])
        # Check minimum size of box.
        if box.area < preprocessor_conf.box_min_size:
            continue
        # Sussy box. Discard if it's too small.
        if data["language"] == "unknown" and box.area < preprocessor_conf.suspicious_box_min_size:
            continue

        boxes.append(box)

    # Sort boxes by their x+y coordinates, using the top right corner as the reference.
    boxes.sort(key=lambda b: b.y1 - 0.4 * b.x2)

    page_data = st.PageData(image_path, mask_path, original_path, scale, boxes, [], [], [])

    # Merge boxes that have mutually overlapping centers.
    page_data.resolve_total_overlaps()

    # Pad the boxes a bit, save a copy, and then pad them some more.
    # The copy is used as a smaller mask, and the padded copy is used as a larger mask.
    page_data.grow_boxes(preprocessor_conf.box_padding_initial, st.BoxType.BOX)
    page_data.right_pad_boxes(preprocessor_conf.box_right_padding_initial, st.BoxType.BOX)

    # Draw the boxes on the image and save it.
    if cache_masks or cache_masks_ocr:
        page_data.visualize(Path(page_data.image_path))

    # Run OCR to discard small boxes that only contain symbols.
    analytic: st.OCRAnalytic | None = None
    if mocr is not None:
        page_data, analytic = ocr_check(
            page_data,
            mocr,
            preprocessor_conf.ocr_max_size,
            preprocessor_conf.ocr_blacklist_pattern,
        )

    # A shallow copy of the box list suffices, because the tuples inside are immutable.
    page_data.extended_boxes = copy(page_data.boxes)

    page_data.grow_boxes(preprocessor_conf.box_padding_extended, st.BoxType.EXTENDED_BOX)
    page_data.right_pad_boxes(preprocessor_conf.box_right_padding_extended, st.BoxType.EXTENDED_BOX)

    # Check for overlapping boxes among the extended boxes.
    # The resulting list is saved in the page_data.merged_extended_boxes attribute.
    page_data.resolve_overlaps(
        from_type=st.BoxType.EXTENDED_BOX,
        to_type=st.BoxType.MERGED_EXT_BOX,
        threshold=preprocessor_conf.box_overlap_threshold,
    )

    # Copy the merged extended boxes to the reference boxes and grow them once again.
    page_data.reference_boxes = copy(page_data.merged_extended_boxes)
    page_data.grow_boxes(preprocessor_conf.box_reference_padding, st.BoxType.REFERENCE_BOX)

    # Write the json file with the cleaned data.
    json_out_path = json_file_path.parent / f"{json_file_path.stem.replace('#raw', '')}#clean.json"

    json_out_path.write_text(page_data.to_json(), encoding="utf-8")

    # Draw the boxes on the image and save it.
    if cache_masks and not cache_masks_ocr:
        page_data.visualize(Path(page_data.image_path), final_boxes=True)

    return analytic


def ocr_check(
    page_data: st.PageData, mocr: MangaOcr, max_box_size: int, ocr_blacklist_pattern: str
) -> tuple[st.PageData, st.OCRAnalytic]:
    """
    Run OCR on small boxes to determine whether they contain mere symbols,
    in which case these boxes do not need to be cleaned and can be removed
    from the dataset.

    The page_data object is modified in place.

    Return analytics data:
    - number of boxes
    - sizes of all boxes that were ocred
    - sizes of the boxes that were removed
    - the cached file name and the text and the box that was removed.

    (Returning the page data isn't strictly necessary, since it's modified in place,
    but this makes that fact more explicit.)

    :param page_data: PageData object containing the data for the page.
    :param mocr: Manga ocr object.
    :param max_box_size: Maximum size of a box in pixels, to consider it for ocr.
    :param ocr_blacklist_pattern: Regex pattern to match against the ocr result.
    :return: The modified page data and Analytics data.
    """
    base_image = Image.open(page_data.image_path)
    scale = page_data.scale
    candidate_small_bubbles = [box for box in page_data.boxes if box.area < max_box_size]
    if not candidate_small_bubbles:
        return page_data, st.OCRAnalytic(len(page_data.boxes), (), (), ())
    # Check if the small bubbles only contain symbols.
    # If they do, then they are probably not text.
    # Discard them in that case.
    box_sizes = []
    discarded_box_sizes = []
    discarded_box_texts: list[tuple[Path, str, st.Box]] = []
    for box in candidate_small_bubbles:
        cutout = base_image.crop(box.as_tuple)
        text = mocr(cutout)
        remove = is_not_worth_cleaning(text, ocr_blacklist_pattern)
        box_sizes.append(box.area)
        if remove:
            # When returning the box in the analytics, the coordinates must be scaled
            # back to the original size so they can be used in relation to the original image.
            # They are used for the csv OCR output.
            discarded_box_texts.append((Path(page_data.original_path), text, box.scale(1 / scale)))
            discarded_box_sizes.append(box.area)
            page_data.boxes.remove(box)

    return (
        page_data,
        st.OCRAnalytic(len(page_data.boxes), box_sizes, discarded_box_sizes, discarded_box_texts),
    )


def is_not_worth_cleaning(text: str, blacklist_pattern: str) -> bool:
    """
    Check if the text is not worth cleaning.
    This is the case if the text is empty, or if it only contains symbols.
    Note that this OCR model produces full width characters.

    :param text: Text to check.
    :param blacklist_pattern: Regex pattern to match against the text.
    :return: True if the text is not worth cleaning, False otherwise.
    """
    if re.fullmatch(blacklist_pattern, text):
        return True
    return False
