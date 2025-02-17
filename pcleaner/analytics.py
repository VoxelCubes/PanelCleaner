import itertools
import shutil
from collections import defaultdict
from io import StringIO
from pathlib import Path
from typing import Sequence

import colorama as clr
from attrs import frozen
from natsort import natsorted

import pcleaner.helpers as hp
from pcleaner.helpers import tr
import pcleaner.structures as st
import pcleaner.config as cfg


@frozen
class OCRAnalytic:
    num_boxes: int
    small_box_sizes: Sequence[int]
    removed_box_sizes: Sequence[int]


# I'll admit this file is a mess.
# These bar chart creators should be abstracted into a single implementation, not 3 different ones.


def terminal_width() -> int:
    # Use a fallback of 100 for unsupported terminals.
    width = shutil.get_terminal_size((100, 100)).columns
    # Make sure the width is at least 20, to avoid weirdness.
    return max(width, 20)


def show_ocr_analytics(
    analytics: Sequence[st.OCRAnalytic],
    max_ocr_size: int,
    max_columns: int = 100,
) -> str:
    """
    The analytics are gathered from the OCR pre-processing which has the goal of
    finding small boxes and to check if they contain text worth cleaning.

    The analytics for each page in the list consist of the following:
    - The number of boxes on the page.
    - The sizes of the small boxes.
    - The sizes of the boxes that were removed.
    - list of: The original file path and the removed text and the box it belonged to.

    Various statistics are then shown.

    :param analytics: The analytics gathered from each pre-processed page.
    :param max_ocr_size: The maximum size of a box to be considered small.
    :param max_columns: The maximum number of columns to use for the chart per line.
    :return: The analytics as a string.
    """
    buffer = StringIO()

    num_boxes = sum(a.num_boxes for a in analytics)
    num_small_boxes = sum(len(a.box_sizes_ocr) for a in analytics)
    small_box_sizes = list(itertools.chain.from_iterable(a.box_sizes_ocr for a in analytics))
    removed_box_sizes = list(itertools.chain.from_iterable(a.box_sizes_removed for a in analytics))
    small_box_ratio = f"{num_small_boxes / num_boxes:.0%}" if num_boxes > 0 else tr("N/A")
    removed_box_ratio = f"{len(removed_box_sizes) / num_boxes:.0%}" if num_boxes > 0 else tr("N/A")
    removed_among_small_ratio = (
        f"{len(removed_box_sizes) / num_small_boxes:.0%}" if num_small_boxes > 0 else tr("N/A")
    )
    # Partition the small box sizes into 5 rough size ranges, equally spaced.
    part_size = 500 if max_ocr_size < 500 * 10 else max_ocr_size // 10
    partitioned_small_box_sizes = partition_list(
        small_box_sizes, partition_size=part_size, max_value=max_ocr_size
    )
    partitioned_removed_boxes = partition_list(
        removed_box_sizes, partition_size=part_size, max_value=max_ocr_size
    )
    title = tr("OCR Analytics")
    buffer.write(f"\n{title}\n")
    buffer.write(f"{'━' * len(title)}\n")
    buffer.write(
        tr(
            "Number of boxes: {num_boxes} | "
            "Number of small boxes: {num_small_boxes} ({small_box_ratio})\n"
        ).format(
            num_boxes=num_boxes,
            num_small_boxes=num_small_boxes,
            small_box_ratio=small_box_ratio,
        )
    )
    buffer.write(
        tr(
            "Number of removed boxes: {num_removed} ({removed_box_ratio} total, {removed_among_small_ratio} of small boxes)\n"
        ).format(
            num_removed=len(removed_box_sizes),
            removed_box_ratio=removed_box_ratio,
            removed_among_small_ratio=removed_among_small_ratio,
        )
    )
    if small_box_sizes:
        buffer.write(tr("\nSmall box sizes:\n"))
        buffer.write(
            draw_pretty_ocr_result_chart(
                partitioned_small_box_sizes, partitioned_removed_boxes, max_columns
            )
            + "\n"
        )
    else:
        buffer.write(tr("No not-removed small boxes found.\n"))

    # Build tuples of the form (path, text) for the removed texts.
    # This requires adding the path from the analytic to all the texts.
    removed_paths: list[Path] = []
    removed_texts: list[str] = []
    for analytic in analytics:
        for text, box in analytic.removed_box_data:
            removed_paths.append(analytic.path)
            removed_texts.append(text)

    if removed_paths:
        # Find and then remove the longest common prefix from the file paths.
        removed_paths = hp.trim_prefix_from_paths(removed_paths)
        removed_path_texts = list(zip(removed_paths, removed_texts))
        # Sort by file path.
        removed_path_texts = natsorted(removed_path_texts, key=lambda p: p[0])

        buffer.write(tr("\nRemoved bubbles:\n"))
        for path, text in removed_path_texts:
            buffer.write(tr("Page {path}: {text}\n").format(path=path, text=text))

    buffer.write("\n")

    return buffer.getvalue()


def draw_pretty_ocr_result_chart(
    small_box_data: list[tuple[str, int]],
    removed_box_data: list[tuple[str, int]],
    max_columns: int = 100,
) -> str:
    """
    Draw a pretty stacked bar chart.

    :param small_box_data: The data for the small boxes.
    :param removed_box_data: The data for the removed boxes.
    :param max_columns: The maximum number of columns to use for the chart per line.
    :return: The chart as a string.
    """
    buffer = StringIO()

    data_array = [
        (label, lower, upper)
        for (label, lower), (_, upper) in zip(small_box_data, removed_box_data)
    ]
    max_label_width = max(len(label) for label, _, _ in data_array)
    bar_width = (
        max_columns - max_label_width - 25
    )  # 16 for the spacing and trailing number and padding.
    max_value = max(lower + upper for _, lower, upper in data_array)

    for label, lower, upper in data_array:
        lower_bar = "█" * int((lower - upper) / max_value * bar_width)
        upper_bar = "█" * int(upper / max_value * bar_width)
        buffer.write(
            f"{label:<{max_label_width}}: "
            f"{lower_bar}{clr.Fore.RED}{upper_bar} {upper}{clr.Style.RESET_ALL} / {lower}\n"
        )

    # Show legend.
    buffer.write(
        f"\n█ "
        + tr("Small boxes")
        + f" | {clr.Fore.RED}█ "
        + tr("Removed boxes")
        + f"{clr.Style.RESET_ALL}"
    )

    return buffer.getvalue()


def draw_masker_histogram(data: dict[str, tuple[int, int]], max_columns: int = 100) -> str:
    """
    Draw a histogram of the masker results.

    :param data: A dict of the mask name, (perfect uses, all uses).
    :param max_columns: The maximum number of columns to use for the histogram per line.
    :return: The histogram as a string.
    """

    # Find the maximum value in the data. (at least 1 to avoid division by zero)
    max_value = max(list(map(lambda x: x[1], data.values())))
    max_value = max(max_value, 1)

    # Longest key.
    max_label_width = max(len(k) for k in data.keys())
    bar_width = (
        max_columns - max_label_width - 25
    )  # 16 for the spacing and trailing number and padding.

    buffer = StringIO()

    # Draw the histogram.
    for key, value in data.items():
        # Use a Unicode character for the bar.
        left_bar = "█" * int(value[0] / max_value * bar_width)
        right_bar = "█" * int((value[1] - value[0]) / max_value * bar_width)
        # If both are 0 in length, but one of them isn't 0 in value, draw the right-most one as a sliver.
        if (not right_bar) and value[1] > value[0]:
            right_bar = "▏"
        if (not left_bar) and (not right_bar) and value[0] > 0:
            left_bar = "▏"

        if not key == tr("Failed"):
            buffer.write(
                f"{key:<{max_label_width}}: "
                f"{clr.Fore.CYAN}{left_bar}{clr.Style.RESET_ALL}{right_bar} "
                f"{clr.Fore.CYAN}{value[0]}{clr.Fore.RESET} / {value[1]}\n"
            )
        else:
            buffer.write(
                f"{key:<{max_label_width}}: "
                f"{clr.Fore.RED}{right_bar} {value[1]}{clr.Fore.RESET}\n"
            )

    # Show legend.
    buffer.write(
        f"\n{clr.Fore.CYAN}█ "
        + tr("Perfect")
        + f"{clr.Style.RESET_ALL} | █ "
        + tr("Total")
        + f" | {clr.Fore.RED}█ "
        + tr("Failed")
        + f"{clr.Style.RESET_ALL} \n"
    )

    return buffer.getvalue()


def partition_list(
    data: list[int],
    *,
    partition_size: int = 500,
    min_value: int | None = 0,
    max_value: int | None = None,
) -> list[tuple[str, int]]:
    """
    Partition the list into tuples of the form (range, count).
    The ranges are saved as a string: "0-499", "500-999", etc.
    If no max_value is given, the maximum value in the data is used.
    If min_value is None, the minimum value in the data is used. Otherwise it defaults to 0.

    :param data: The data to partition.
    :param partition_size: [Optional] The size of the partitions. Default: 500.
    :param min_value: [Optional] The minimum value to partition. Default: 0.
    :param max_value: [Optional] The maximum value to partition to. Default: None.
    :return: The partitioned data as a list of tuples.
    """
    if max_value is None:
        max_value = max(data)

    max_label_len = len(str(max_value))

    partition = [
        (
            f"{i * partition_size: >{max_label_len}}-{(i + 1) * partition_size: >{max_label_len}}",
            len([d for d in data if i * partition_size <= d < (i + 1) * partition_size]),
        )
        for i in range(min_value, max_value // partition_size)
    ]

    return partition


def show_masker_analytics(
    analytics: list[st.MaskFittingAnalytic], masker_config: cfg.MaskerConfig, max_columns: int = 100
) -> str:
    """
    Present the analytics gathered from the masking process.

    :param analytics: The analytics gathered from each page.
    :param masker_config: The masker configuration used to gather the analytics.
    :param max_columns: The maximum number of columns to use for the chart per line.
    :return: The analytics as a string.
    """
    buffer = StringIO()

    total_boxes = len(analytics)
    masks_succeeded = sum(1 for analytic in analytics if analytic.fit_was_found)
    perfect_masks = sum(
        1 for analytic in analytics if analytic.fit_was_found and analytic.mask_std_deviation == 0
    )
    average_border_deviation = (
        f"{sum(analytic.mask_std_deviation for analytic in analytics if analytic.fit_was_found) / masks_succeeded:.2f}"
        if masks_succeeded
        else tr("N/A")
    )
    success_rate = f"{masks_succeeded / total_boxes:.0%}" if total_boxes else tr("N/A")
    perfect_mask_rate = f"{perfect_masks / masks_succeeded:.0%}" if masks_succeeded else tr("N/A")
    masks_failed = total_boxes - masks_succeeded

    # Count how many times each mask thickness was used.
    mask_usage_by_thickness: defaultdict[int | None, int] = defaultdict(int)
    perfect_mask_usage_by_thickness: defaultdict[int | None, int] = defaultdict(int)
    for analytic in analytics:
        if analytic.fit_was_found:
            mask_usage_by_thickness[analytic.mask_thickness] += 1
            if analytic.mask_std_deviation == 0:
                perfect_mask_usage_by_thickness[analytic.mask_thickness] += 1

    # Write the analytics.
    title = tr("Mask Fitment Analytics")
    buffer.write(f"\n{title}\n")
    buffer.write(f"{'━' * len(title)}\n")
    buffer.write(
        tr("Total boxes")
        + f": {total_boxes} | "
        + tr("Masks succeeded")
        + f": {masks_succeeded} ({success_rate}) | "
        + tr("Masks failed")
        + f": {clr.Fore.RED}{masks_failed}{clr.Fore.RESET}\n"
    )
    buffer.write(
        tr("Perfect masks")
        + f": {clr.Fore.CYAN}{perfect_masks}{clr.Fore.RESET} ({perfect_mask_rate}) | "
        + tr("Average border deviation")
        + f": {average_border_deviation}\n"
    )
    buffer.write(tr("\nMask usage by thickness (in pixels):\n"))

    # Quit being retarded over mixed types in a list, this is Python for fuck's sake.
    # noinspection PyTypeChecker
    thicknesses: list[int | None] = list(
        range(
            masker_config.min_mask_thickness,
            masker_config.min_mask_thickness
            + masker_config.mask_growth_step_pixels * masker_config.mask_growth_steps,
            masker_config.mask_growth_step_pixels,
        )
    ) + [None]
    # Prepare histogram data: label, (perfect, total)
    mask_usages_dict: dict[str, tuple[int, int]] = {}
    for thickness in thicknesses:
        if thickness is not None:
            label = tr("Mask ({thickness}px)").format(thickness=thickness)
        else:
            label = tr("Box mask")

        perfect = perfect_mask_usage_by_thickness[thickness]
        total = mask_usage_by_thickness[thickness]

        mask_usages_dict[label] = (perfect, total)

    # Add failed masks to the histogram.
    mask_usages_dict[tr("Failed")] = (0, masks_failed)

    buffer.write(draw_masker_histogram(mask_usages_dict, max_columns) + "\n")

    pages_with_success_and_fails_dict: defaultdict[Path, defaultdict[str, int]] = defaultdict(
        lambda: defaultdict(int)
    )
    for analytic in analytics:
        pages_with_success_and_fails_dict[analytic.image_path][
            "succeeded" if analytic.fit_was_found else "failed"
        ] += 1

    if not pages_with_success_and_fails_dict:
        buffer.write(tr("All bubbles were successfully masked.\n"))
        return buffer.getvalue()

    pages_with_success_and_fails: list[tuple[Path, int, int]] = [
        (page_path, counts["succeeded"], counts["failed"])
        for page_path, counts in pages_with_success_and_fails_dict.items()
        if counts["failed"]
    ]

    if pages_with_success_and_fails:
        page_paths, succeeded_counts, failed_counts = zip(*pages_with_success_and_fails)
        page_paths = hp.trim_prefix_from_paths(page_paths)
        pages_with_success_and_fails = list(zip(page_paths, succeeded_counts, failed_counts))
        pages_with_success_and_fails = natsorted(pages_with_success_and_fails, key=lambda x: x[0])

    buffer.write(tr("\nPages with failures / total:\n"))
    for page_path, succeeded, failed in pages_with_success_and_fails:
        buffer.write(f"{page_path}: {clr.Fore.RED}{failed}{clr.Fore.RESET} / {succeeded+failed}\n")

    buffer.write("\n")

    return buffer.getvalue()


def show_denoise_analytics(
    analytics: list[st.DenoiseAnalytic],
    configured_deviation_threshold: float,
    max_deviation_threshold: float,
    max_columns: int = 100,
) -> str:
    """
    Present the analytics gathered from the denoising process.

    :param analytics: The analytics gathered from each page, here standard deviations.
    :param configured_deviation_threshold: The configured deviation threshold to de denoising.
    :param max_deviation_threshold: The maximum deviation threshold to discard the mask.
    :param max_columns: The maximum number of columns to use for the chart per line.
    :return: The analytics as a string.
    """
    buffer = StringIO()

    title = tr("Denoising Analytics")
    buffer.write(f"\n{title}\n")
    buffer.write(f"{'━' * len(title)}\n")

    # Get the standard deviations into one single list.
    std_deviations: list[float] = [
        *itertools.chain.from_iterable(analytic.std_deviations for analytic in analytics)
    ]

    # Split the standard deviations into two lists: one for the ones that were below the threshold,
    # and one for the ones that were above the threshold.
    below_threshold = [
        std_dev for std_dev in std_deviations if std_dev <= configured_deviation_threshold
    ]
    above_threshold = [
        std_dev for std_dev in std_deviations if std_dev > configured_deviation_threshold
    ]

    total_masks = len(std_deviations)
    above_threshold_count = len(above_threshold)
    above_ratio = f"{above_threshold_count / total_masks:.0%}" if total_masks else tr("N/A")

    buffer.write(
        tr("Total masks")
        + f": {total_masks} | "
        + tr("Masks denoised")
        + f": {clr.Fore.MAGENTA}{above_threshold_count}{clr.Fore.RESET} ({above_ratio})\n"
    )
    buffer.write(
        tr("Minimum deviation to denoise")
        + f": {configured_deviation_threshold} | "
        + tr("Maximum allowed deviation")
        + f": {max_deviation_threshold}\n"
    )
    buffer.write(tr("Standard deviation around masks:\n\n"))

    # Show the lists in a graph.
    buffer.write(
        draw_denoise_histogram(
            below_threshold,
            above_threshold,
            max_deviation_threshold,
            max_columns,
        )
        + "\n"
    )
    buffer.write("\n")

    return buffer.getvalue()


def draw_denoise_histogram(
    below_threshold: list[float],
    above_threshold: list[float],
    max_value: float,
    max_columns: int = 100,
) -> str:
    """
    Draw a histogram of the deviations.

    :param below_threshold: The standard deviations that were below the threshold.
    :param above_threshold: The standard deviations that were above the threshold.
    :param max_value: The maximum deviation threshold to discard the mask.
    :param max_columns: The maximum number of columns to use for the histogram per line.
    :return: The histogram as a string.
    """
    # Partition the values into 10 buckets.
    # Use a cubic polynomial that passes through 0 and the max value.
    # The polynomial is a simple f(x) = ax^3, meaning the coefficient a
    # must be max_value/10^3.
    exponent = 3
    cubic_coefficient = max_value / 10**exponent
    # The buckets contain: (min, max)
    bucket_ranges = (
        (cubic_coefficient * (i - 1) ** exponent, cubic_coefficient * i**exponent)
        for i in range(1, 11)
    )
    # Set the precision so that the second bucket isn't 0.
    # Basically, if the value is 0.00143, we want a precision of 3 to still see that 1.
    second_bucket_min = str(cubic_coefficient * 1**exponent).split(".")[1]
    # Count the zeroes from the left, and add 1 to only show up to the first non-zero digit.
    precision = len(second_bucket_min) - len(second_bucket_min.lstrip("0")) + 1
    # The buckets contain: (min, max, count_below_threshold, count_above_threshold)
    buckets: list[tuple[str, str, int, int]] = [
        (
            f"{b_min:.{precision}f}",
            f"{b_max:.{precision}f}",
            sum(1 for std_dev in below_threshold if b_min <= std_dev < b_max),
            sum(1 for std_dev in above_threshold if b_min <= std_dev < b_max),
        )
        for b_min, b_max in bucket_ranges
    ]
    # Format the ranges to look better.
    number_width = len(str(f"{max_value:.{precision}f}"))
    buckets_labeled: list[tuple[str, int, int]] = [
        (
            f"{b_min: >{number_width}}-{b_max: >{number_width}}",
            below,
            above,
        )
        for b_min, b_max, below, above in buckets
    ]
    # Get the maximum count in the buckets to rescale them.
    max_count = max((below + above for _, below, above in buckets_labeled))
    max_count = max(max_count, 1)
    # Rescale the buckets.

    max_label_length = max(len(label) for label, _, _ in buckets_labeled)
    bar_width = max_columns - max_label_length - 28  # 28 is for the spaces and the brackets.

    bucket_bar_lengths: list[tuple[int, int]] = [
        (int(below * bar_width / max_count), int(above * bar_width / max_count))
        for _, below, above in buckets_labeled
    ]

    buffer = StringIO()
    # Draw the buckets.
    for (b_range, below, above), (below_len, above_len) in zip(buckets_labeled, bucket_bar_lengths):
        left_bar = "█" * below_len
        right_bar = "█" * above_len
        if (not above_len) and above:
            right_bar = "▏"
        if (not right_bar) and (not left_bar) and below:
            left_bar = "▏"

        buffer.write(
            f"{b_range} : {left_bar}{clr.Fore.MAGENTA}{right_bar} {above}{clr.Fore.RESET} / {below+above}\n"
        )

    # Draw the legend.
    buffer.write(
        f"\n{clr.Fore.MAGENTA}█ " + tr("Denoised") + f"{clr.Fore.RESET} | █ " + tr("Total\n")
    )
    return buffer.getvalue()


def show_inpainting_analytics(
    analytics: list[st.InpaintingAnalytic],
    minimum_thickness: int,
    maximum_thickness: int,
    max_columns: int = 100,
) -> str:
    """
    Present the analytics gathered from the inpainting process.

    :param analytics: The analytics gathered from each page, here standard deviations.
    :param minimum_thickness: The minimum thickness of the inpainted outlines.
    :param maximum_thickness: The maximum thickness of the inpainted outlines.
    :param max_columns: The maximum number of columns to use for the chart per line.
    :return: The analytics as a string.
    """
    buffer = StringIO()

    title = tr("Inpainting Analytics")
    buffer.write(f"\n{title}\n")
    buffer.write(f"{'━' * len(title)}\n")

    # Get the thicknesses into one single list.
    thicknesses: list[int] = [
        *itertools.chain.from_iterable(analytic.thicknesses for analytic in analytics)
    ]

    total_inpaint = len(thicknesses)
    average_thickness = f"{sum(thicknesses) / total_inpaint:.0%}" if total_inpaint else tr("N/A")

    buffer.write(
        tr("Inpainting performed")
        + f": {total_inpaint} | "
        + tr("Average thickness")
        + f": {average_thickness}\n"
    )
    buffer.write(
        tr("Minimum thickness")
        + f": {minimum_thickness} | "
        + tr("Maximum thickness")
        + f": {maximum_thickness}\n"
    )
    buffer.write(tr("Outline thickness around text inpainted:\n\n"))

    # Show the lists in a graph.
    buffer.write(
        draw_inpaint_histogram(
            thicknesses,
            minimum_thickness,
            maximum_thickness,
            max_columns,
        )
        + "\n"
    )
    buffer.write("\n")

    return buffer.getvalue()


def draw_inpaint_histogram(
    thicknesses: list[int],
    minimum_thickness: int,
    maximum_thickness: int,
    max_columns: int = 100,
) -> str:
    """
    Draw a histogram of the deviations.

    :param thicknesses: The thicknesses of the inpainted outlines.
    :param minimum_thickness: The minimum thickness of the inpainted outlines.
    :param maximum_thickness: The maximum thickness of the inpainted outlines.
    :param max_columns: The maximum number of columns to use for the histogram per line.
    :return: The histogram as a string.
    """
    # The buckets contain: (min, count)
    buckets: list[tuple[int, int]] = []
    for thickness in range(minimum_thickness, maximum_thickness + 1):
        buckets.append((thickness, thicknesses.count(thickness)))
    # Format the ranges to look better.
    number_width = len(str(buckets[-1][0]))
    buckets_labeled: list[tuple[str, int]] = [
        (
            f"{thiccness: >{number_width}}",
            count,
        )
        for thiccness, count in buckets
    ]
    # Get the maximum count in the buckets to rescale them.
    max_count = max((count for _, count in buckets_labeled))
    max_count = max(max_count, 1)
    # Rescale the buckets.

    max_label_length = max(len(label) for label, _ in buckets_labeled)
    bar_width = max_columns - max_label_length - 28  # 28 is for the spaces and the brackets.

    bucket_bar_lengths: list[int] = [
        int(count * bar_width / max_count) for _, count in buckets_labeled
    ]

    buffer = StringIO()
    # Draw the buckets.
    for (b_range, count), (count_len) in zip(buckets_labeled, bucket_bar_lengths):
        bar = "█" * count_len
        if (not count_len) and count:
            bar = "▏"

        buffer.write(f"{b_range} : {clr.Fore.LIGHTGREEN_EX}{bar} {count}{clr.Fore.RESET}\n")

    # Draw the legend.
    buffer.write(f"\n{clr.Fore.LIGHTGREEN_EX}█ " + tr("Inpainted") + clr.Fore.RESET + "\n")

    return buffer.getvalue()
