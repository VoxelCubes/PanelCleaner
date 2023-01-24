import json
import re
from dataclasses import asdict
from pathlib import Path

from PIL import Image
from manga_ocr import MangaOcr

import pcleaner.ctd_interface as ctm
import pcleaner.structures as st
import pcleaner.config as cfg


def generate_mask_data(image_path: list[Path], model_path: Path, output_dir: Path) -> None:
    """
    Run the ai model to generate masks and box data for the given image,
    or all images in the given directory.

    :param image_path: Path to the image or directory of images.
    :param model_path: Path to the model file.
    :param output_dir: Path to the directory where the results will be saved.
    """

    ctm.model2annotations(model_path, image_path, output_dir)


def prep_json_file(
    json_file_path: Path,
    pre_processor_conf: cfg.PreProcessorConfig,
    cache_masks: bool,
    mocr: MangaOcr | None = None,
) -> tuple[int, tuple[int, ...], tuple[int, ...], tuple[tuple[str, str], ...]] | None:
    """
    Load the generated json file, and clean the data, leaving only the
    relevant data for the following steps.

    Check that this file wasn't already processed, and if it was, skip it.
    Processed json files have the file name ending with '_clean.json'.

    If a manga ocr object is given, run ocr on small boxes to determine whether
    they contain mere symbols, in which case these boxes do not need to be cleaned
    and can be removed from the dataset.
    The model must be initialized somewhere else to lessen coupling, and to avoid the long
    initialization time for each page.

    Analytics data is returned if the manga ocr object is given.

    :param json_file_path: Path to the json file.
    :param pre_processor_conf: Pre processor configuration, part of the profile.
    :param cache_masks: Whether to cache the masks.
    :param mocr: [Optional] Manga ocr object.
    :return: Analytics data if the manga ocr object is given, None otherwise.
    """
    # Check if the file was already processed.
    if json_file_path.name.endswith("_clean.json"):
        return
    if json_file_path.name.endswith("_mask_data.json"):
        return

    json_data = json.loads(json_file_path.read_text())

    image_path = json_data["image_path"]
    mask_path = json_data["mask_path"]
    original_path = json_data["original_path"]
    boxes = []

    for data in json_data["blk_list"]:
        # Check minimum size of box.
        x1, y1, x2, y2 = data["xyxy"]
        box_size = (x2 - x1) * (y2 - y1)
        if box_size > pre_processor_conf.box_min_size:
            # Sussy box. Discard if it's too small.
            if (
                data["language"] == "unknown"
                and box_size < pre_processor_conf.suspicious_box_min_size
            ):
                continue
            boxes.append(data["xyxy"])

    page_data = st.PageData(image_path, mask_path, original_path, boxes, [], [], [])

    # Run OCR to discard small boxes that only contain symbols.
    analytics = None
    if mocr is not None:
        page_data, analytics = ocr_check(
            page_data,
            mocr,
            pre_processor_conf.ocr_max_size,
            pre_processor_conf.ocr_blacklist_pattern,
        )

    # Pad the boxes a bit, save a copy, and then pad them some more.
    # The copy is used as a smaller mask, and the padded copy is used as a larger mask.
    page_data.grow_boxes(pre_processor_conf.box_padding_initial, st.BoxType.BOX)
    page_data.right_pad_boxes(pre_processor_conf.box_right_padding_initial, st.BoxType.BOX)

    # A shallow copy of the box list suffices, because the tuples inside are immutable.
    page_data.extended_boxes = page_data.boxes.copy()

    page_data.grow_boxes(pre_processor_conf.box_padding_extended, st.BoxType.EXTENDED_BOX)
    page_data.right_pad_boxes(
        pre_processor_conf.box_right_padding_extended, st.BoxType.EXTENDED_BOX
    )

    # Check for overlapping boxes among the extended boxes.
    # The resulting list is saved in the page_data.merged_extended_boxes attribute.
    page_data.resolve_overlaps()

    # Copy the merged extended boxes to the reference boxes and grow them once again.
    page_data.reference_boxes = page_data.merged_extended_boxes.copy()
    page_data.grow_boxes(pre_processor_conf.box_reference_padding, st.BoxType.REFERENCE_BOX)

    # Write the json file with the cleaned data.
    json_out_path = json_file_path.parent / f"{json_file_path.stem}_clean.json"
    # Remove the _image_size attribute, because it's a cached value that may be unset.
    page_data_dict = asdict(page_data)
    del page_data_dict["_image_size"]
    json_out_path.write_text(json.dumps(page_data_dict, indent=4))

    # Draw the boxes on the image and save it.
    if cache_masks:
        page_data.visualize(Path(page_data.image_path))

    return analytics


def ocr_check(
    page_data: st.PageData, mocr: MangaOcr, max_box_size: int, ocr_blacklist_pattern: str
) -> tuple[st.PageData, tuple[int, tuple[int, ...], tuple[int, ...], tuple[tuple[str, str], ...]]]:
    """
    Run OCR on small boxes to determine whether they contain mere symbols,
    in which case these boxes do not need to be cleaned and can be removed
    from the dataset.

    The page_data object is modified in place.

    Return analytics data:
    - number of boxes
    - sizes of all boxes that were ocred
    - sizes of the boxes that were removed
    - the cached file name and the text of the boxes that were removed.

    (Returning the page data isn't strictly necessary, since it's modified in place,
    but this makes that fact more explicit.)

    :param page_data: PageData object containing the data for the page.
    :param mocr: Manga ocr object.
    :param max_box_size: Maximum size of a box in pixels, to consider it for ocr.
    :param ocr_blacklist_pattern: Regex pattern to match against the ocr result.
    :return: The modified page data and Analytics data.
    """
    base_image = Image.open(page_data.image_path)
    candidate_small_bubbles = [
        box for box in page_data.boxes if page_data.box_size(box) < max_box_size
    ]
    if not candidate_small_bubbles:
        return page_data, (len(page_data.boxes), (), (), ())
    # Check if the small bubbles only contain symbols.
    # If they do, then they are probably not text.
    # Discard them in that case.
    box_sizes = []
    discarded_box_sizes = []
    discarded_box_texts: list[tuple[str, str]] = []
    for box in candidate_small_bubbles:
        cutout = base_image.crop(box)
        text = mocr(cutout)
        remove = is_not_worth_cleaning(text, ocr_blacklist_pattern)
        box_size = page_data.box_size(box)
        box_sizes.append(box_size)
        if remove:
            discarded_box_texts.append((page_data.original_path, text))
            discarded_box_sizes.append(box_size)
            page_data.boxes.remove(box)

    return page_data, (
        len(page_data.boxes) + len(discarded_box_sizes),
        tuple(box_sizes),
        tuple(discarded_box_sizes),
        tuple(discarded_box_texts),
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
