import json
import re
from collections import Counter
from copy import copy
from pathlib import Path

from PIL import Image
from loguru import logger

import pcleaner.config as cfg
import pcleaner.ctd_interface as ctm
import pcleaner.ocr.ocr as ocr
import pcleaner.ocr.supported_languages as osl
import pcleaner.output_structures as ost
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


# adapted from https://maxhalford.github.io/blog/comic-book-panel-segmentation/
# Original algorithm was used to sort panels in reading order, adapted here for balloons,
# but balloons reading order is a problem that can't really be solved until we can
# segment the page into panels.
def are_boxes_aligned(a: st.Box, b: st.Box, axis: int, tolerance: int = 10) -> bool:
    if axis == 0:  # Horizontal axis, consider vertical alignment with tolerance
        return (a.y1 - tolerance) < b.y2 and (b.y1 - tolerance) < a.y2
    else:  # Vertical axis, consider horizontal alignment with tolerance
        return (a.x1 - tolerance) < b.x2 and (b.x1 - tolerance) < a.x2


def cluster_boxes(
    bboxes: list[st.Box], axis: int = 0, tolerance: int = 10, depth: int = 0
) -> list[list[st.Box]]:
    if depth > 10:  # Base case to prevent infinite recursion
        return [bboxes]

    clusters = []
    for bbox in bboxes:
        for cluster in clusters:
            if any(are_boxes_aligned(b, bbox, axis=axis, tolerance=tolerance) for b in cluster):
                cluster.append(bbox)
                break
        else:
            clusters.append([bbox])

    # Sort clusters based on the first box in each cluster
    if axis == 0:  # Horizontal axis, sort by top edge (y1)
        clusters.sort(key=lambda c: c[0].y1)
    else:  # Vertical axis, sort by left edge (x1)
        clusters.sort(key=lambda c: c[0].x1)

    # Recursively cluster within each cluster, flipping axis and passing tolerance
    for i, cluster in enumerate(clusters):
        if len(cluster) > 1:
            clusters[i] = cluster_boxes(
                cluster, axis=1 if axis == 0 else 0, tolerance=tolerance, depth=depth + 1
            )

    return clusters


def flatten(l):
    for el in l:
        if isinstance(el, list):
            yield from flatten(el)
        else:
            yield el


# Adaption end.


def prep_json_file(
    json_file_path: Path,
    preprocessor_conf: cfg.PreprocessorConfig,
    cache_masks: bool,
    ocr_engine_factory: ocr.OCREngineFactory | None = None,
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
    :param ocr_engine_factory: [Optional] OCR processors mapping.
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
    box_langs: list[osl.LanguageCode | None] = []

    path_gen = ost.OutputPathGenerator(Path(original_path), Path(mask_path).parent, Path(mask_path))

    # Map the box language codes to the language codes used in the ocr module.
    if preprocessor_conf.ocr_language in (
        osl.LanguageCode.detect_box,
        osl.LanguageCode.detect_page,
    ):
        # Map the raw detected languages to language codes.
        for data in json_data["blk_list"]:
            if data["language"] == "ja":
                data["language"] = osl.LanguageCode.jpn
            elif data["language"] == "eng":
                data["language"] = osl.LanguageCode.eng
            elif data["language"] == "unknown":
                data["language"] = None
            else:
                logger.warning(f"Unknown language code: {data['language']} detected in a box!")
                data["language"] = None
    else:
        # The user wants to overwrite the detected languages with a specific language.
        for data in json_data["blk_list"]:
            data["language"] = preprocessor_conf.ocr_language

    # Filter boxes based on the language and size.
    for data in json_data["blk_list"]:
        # If we plan to do ocr but can't detect the language, skip it if being strict.
        if performing_ocr and data["language"] is None and preprocessor_conf.ocr_strict_language:
            continue

        box = st.Box(*data["xyxy"])
        # Check minimum size of box.
        if box.area < preprocessor_conf.box_min_size:
            continue
        # Sussy box. Discard if it's too small.
        if data["language"] is None and box.area < preprocessor_conf.suspicious_box_min_size:
            continue

        box_langs.append(data["language"])
        boxes.append(box)

    # Prioritize non-None languages when choosing the most prominent one.
    box_langs_without_none = [lang for lang in box_langs if lang is not None]
    page_lang: osl.LanguageCode | None = (
        Counter(box_langs_without_none).most_common(1)[0][0] if box_langs_without_none else None
    )

    if preprocessor_conf.ocr_language == osl.LanguageCode.detect_page:
        logger.debug(f"Detected page language: {page_lang} for page: {original_path}")
        box_langs = [page_lang] * len(boxes)

    page_data = st.PageData(
        image_path, mask_path, original_path, scale, box_langs, boxes, [], [], []
    )

    # Merge boxes that have mutually overlapping centers.
    page_data.resolve_total_overlaps()

    # Pad the boxes a bit, save a copy, and then pad them some more.
    # The copy is used as a smaller mask, and the padded copy is used as a larger mask.
    page_data.grow_boxes(preprocessor_conf.box_padding_initial, st.BoxType.BOX)
    page_data.right_pad_boxes(preprocessor_conf.box_right_padding_initial, st.BoxType.BOX)

    reading_order = preprocessor_conf.reading_order
    x_factor = -0.4
    y_factor = 1
    # Check if we're dealing with left-to-right reading order.
    if (reading_order == cfg.ReadingOrder.COMIC) or (
        page_lang not in osl.LANGUAGES_RTL_BOX_ORDER and reading_order == cfg.ReadingOrder.AUTO
    ):
        x_factor *= -1

    # Keep the boxes and their langs synchronized.
    if len(page_data.boxes) > 1:
        page_data.boxes, page_data.box_language = zip(
            *sorted(
                zip(page_data.boxes, page_data.box_language),
                key=lambda x: x_factor * x[0].x1 + y_factor * x[0].y1,
            )
        )
    # Convert the returned tuples back to lists.
    page_data.boxes = list(page_data.boxes)
    page_data.box_language = list(page_data.box_language)

    # Draw the boxes on the image and save it.
    if cache_masks or cache_masks_ocr:
        page_data.visualize(page_data.image_path, path_gen.boxes)

    # Run OCR to discard small boxes that only contain symbols.
    analytic: st.OCRAnalytic | None = None
    if ocr_engine_factory is not None:
        page_data, analytic = ocr_check(
            page_data,
            ocr_engine_factory,
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
    json_out_path = path_gen.clean_json

    json_out_path.write_text(page_data.to_json(), encoding="utf-8")

    # Draw the boxes on the image and save it.
    if cache_masks and not cache_masks_ocr:
        page_data.visualize(page_data.image_path, path_gen.final_boxes)

    return analytic


def ocr_check(
    page_data: st.PageData,
    ocr_engine_factory: ocr.OCREngineFactory,
    max_box_size: int,
    ocr_blacklist_pattern: str,
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
    :param ocr_engine_factory: OCR processors mapping.
    :param max_box_size: Maximum size of a box in pixels, to consider it for ocr.
    :param ocr_blacklist_pattern: Regex pattern to match against the ocr result.
    :return: The modified page data and Analytics data.
    """
    base_image = Image.open(page_data.image_path)
    scale: float = page_data.scale
    langs: list[osl.LanguageCode | None] = page_data.box_language
    boxes: list[st.Box | None] = page_data.boxes

    # candidate_small_bubbles = list(filter(lambda x: x[0].area < max_box_size, bubbles))
    candidate_small_bubble_indices = [i for i, box in enumerate(boxes) if box.area < max_box_size]
    if not candidate_small_bubble_indices:
        return page_data, st.OCRAnalytic(Path(page_data.original_path), len(boxes), (), (), ())
    # Check if the small bubbles only contain symbols.
    # If they do, then they are probably not text. Discard them in that case.
    box_sizes = []
    discarded_box_sizes = []
    discarded_box_texts: list[tuple[str, st.Box]] = []
    for i in candidate_small_bubble_indices:
        box = boxes[i]
        lang = langs[i]
        cutout = base_image.crop(box.as_tuple)
        ocr_engine = ocr_engine_factory(lang)
        text = ocr_engine(cutout)
        remove = is_not_worth_cleaning(text, ocr_blacklist_pattern)
        box_sizes.append(box.area)
        if remove:
            # When returning the box in the analytics, the coordinates must be scaled
            # back to the original size so they can be used in relation to the original image.
            # They are used for the csv OCR output.
            discarded_box_texts.append((text, box.scale(1 / scale)))
            discarded_box_sizes.append(box.area)
            # Overwrite the box and lang in the page data, to not break the iterator.
            boxes[i] = None
            langs[i] = None

    # Remove the None values from the boxes and langs lists.
    page_data.boxes = [box for box in boxes if box is not None]
    page_data.box_language = [lang for lang in langs if lang is not None]

    return (
        page_data,
        st.OCRAnalytic(
            Path(page_data.original_path),
            len(boxes),
            box_sizes,
            discarded_box_sizes,
            discarded_box_texts,
        ),
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
    if re.fullmatch(blacklist_pattern, text, re.DOTALL):
        return True
    return False
