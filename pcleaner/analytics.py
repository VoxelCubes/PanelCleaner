import itertools
import shutil
from collections import defaultdict
from pathlib import Path

import colorama as clr
from natsort import natsorted

import pcleaner.structures as st


def terminal_width() -> int:
    # Use a fallback of 50 for unsupported terminals.
    width = shutil.get_terminal_size((50, 50)).columns
    # Make sure the width is at least 20, to avoid weirdness.
    return max(width, 20)


def show_ocr_analytics(
    analytics: list[tuple[int, tuple[int, ...], tuple[int, ...], tuple[tuple[str, str], ...]]],
    max_ocr_size: int,
) -> None:
    """
    The analytics are gathered from the OCR pre-processing which has the goal of
    finding small boxes and to check if they contain text worth cleaning.

    The analytics for each page in the list consist of the following:
    - The number of boxes on the page.
    - The sizes of the small boxes.
    - The sizes of the boxes that were removed.
    - The original file path and the removed text.

    Various statistics are then shown.

    :param analytics: The analytics gathered from each pre-processed page.
    :param max_ocr_size: The maximum size of a box to be considered small.
    """
    num_boxes = sum(a[0] for a in analytics)
    num_small_boxes = sum(len(a[1]) for a in analytics)
    small_box_sizes = list(itertools.chain.from_iterable(a[1] for a in analytics))
    removed_box_sizes = list(itertools.chain.from_iterable(a[2] for a in analytics))
    small_box_ratio = f"{num_small_boxes / num_boxes:.0%}" if num_boxes > 0 else "N/A"
    removed_box_ratio = f"{len(removed_box_sizes) / num_boxes:.0%}" if num_boxes > 0 else "N/A"
    removed_among_small_ratio = (
        f"{len(removed_box_sizes) / num_small_boxes:.0%}" if num_small_boxes > 0 else "N/A"
    )
    # Partition the small box sizes into 5 rough size ranges, equally spaced.
    part_size = 500 if max_ocr_size < 500 * 10 else max_ocr_size // 10
    partitioned_small_box_sizes = partition_list(
        small_box_sizes, partition_size=part_size, max_value=max_ocr_size
    )
    partitioned_removed_boxes = partition_list(
        removed_box_sizes, partition_size=part_size, max_value=max_ocr_size
    )
    print("\nOCR Analytics")
    print("-------------")
    print(
        f"Number of boxes: {num_boxes} | "
        f"Number of small boxes: {num_small_boxes} ({small_box_ratio})"
    )
    print(
        f"Number of removed boxes: {len(removed_box_sizes)} ({removed_box_ratio} total, {removed_among_small_ratio} of small boxes)"
    )
    if small_box_sizes:
        print("\nSmall box sizes:")
        draw_pretty_ocr_result_chart(partitioned_small_box_sizes, partitioned_removed_boxes)
    else:
        print("No not-removed small boxes found.\n")

    # Show removed texts.
    removed_texts = list(itertools.chain.from_iterable(a[3] for a in analytics))

    # Find and then remove the longest common prefix from the file paths.
    prefix = longest_common_prefix([str(Path(path).parent) for path, _ in removed_texts])
    if prefix:
        removed_texts = [(path[len(prefix) :], text) for path, text in removed_texts]
    # Remove a rogue / or \ from the start of the path, if they all have one.
    if all(path.startswith("/") or path.startswith("\\") for path, _ in removed_texts):
        removed_texts = [(path[1:], text) for path, text in removed_texts]

    removed_texts = natsorted(removed_texts, key=lambda x: x[0])

    print("\nRemoved bubbles:")
    for path, text in removed_texts:
        print(f"Page {path}: {text}")

    print("\n")


def draw_pretty_ocr_result_chart(
    small_box_data: list[tuple[str, int]], removed_box_data: list[tuple[str, int]]
) -> None:
    """
    Draw a pretty stacked bar chart.

    :param small_box_data: The data for the small boxes.
    :param removed_box_data: The data for the removed boxes.
    """
    width = terminal_width()
    data_array = [
        (label, lower, upper)
        for (label, lower), (_, upper) in zip(small_box_data, removed_box_data)
    ]
    max_label_width = max(len(label) for label, _, _ in data_array)
    bar_width = width - max_label_width - 16  # 16 for the spacing and trailing number and padding.
    max_value = max(lower + upper for _, lower, upper in data_array)

    for label, lower, upper in data_array:
        lower_bar = "█" * int((lower - upper) / max_value * bar_width)
        upper_bar = "█" * int(upper / max_value * bar_width)
        print(
            f"{label:<{max_label_width}}: "
            f"{lower_bar}{clr.Fore.RED}{upper_bar} {upper}{clr.Style.RESET_ALL} / {lower}"
        )

    # Show legend.
    print(f"\n█ Small boxes | {clr.Fore.RED}█ Removed boxes{clr.Style.RESET_ALL}")


def draw_cleaner_histogram(data: dict[str, tuple[int, int]]) -> None:
    """
    Draw a histogram of the cleaner results.

    :param data: A dict of the mask name, (perfect uses, all uses).
    """

    width = terminal_width()
    # Find the maximum value in the data. (at least 1 to avoid division by zero)
    max_value = max(list(map(lambda x: x[1], data.values())))
    max_value = max(max_value, 1)

    # Longest key.
    max_label_width = max(len(k) for k in data.keys())
    bar_width = width - max_label_width - 16  # 16 for the spacing and trailing number and padding.

    # Draw the histogram.
    for key, value in data.items():
        # Use a Unicode character for the bar.
        left_bar = "█" * int(value[0] / max_value * bar_width)
        right_bar = "█" * int((value[1] - value[0]) / max_value * bar_width)
        # If both are 0 in length, but one of them isn't 0 in value, draw the right-most one as a sliver.
        if not left_bar and not right_bar and value[1] > value[0]:
            right_bar = "▏"
        elif not left_bar and not right_bar and value[0] > 0:
            left_bar = "▏"

        print(
            f"{key:<{max_label_width}}: "
            f"{clr.Fore.CYAN}{left_bar}{clr.Style.RESET_ALL}{right_bar} "
            f"{clr.Fore.CYAN}{value[0]}{clr.Fore.RESET} / {value[1]}"
        )

    # Show legend.
    print(f"\n{clr.Fore.CYAN}█ Perfect{clr.Style.RESET_ALL} | █ Total")


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


def show_cleaner_analytics(analytics: list[tuple[Path, bool, int, float]]):
    """
    Present the analytics gathered from the cleaning process.

    The analytics for each page in the list consist of the following tuple:
    list[original_image_path, mask_found, mask_index, border_deviation]

    :param analytics: The analytics gathered from each page.
    """

    total_boxes = len(analytics)
    masks_succeeded = sum(1 for analytics in analytics if analytics[1])
    perfect_masks = sum(1 for analytics in analytics if analytics[1] and analytics[3] == 0)
    average_border_deviation = (
        f"{sum(analytics[3] for analytics in analytics if analytics[1]) / masks_succeeded:.2f}"
        if masks_succeeded
        else "N/A"
    )
    success_rate = f"{masks_succeeded / total_boxes:.0%}" if total_boxes else "N/A"
    perfect_mask_rate = f"{perfect_masks / total_boxes:.0%}" if total_boxes else "N/A"
    masks_failed = total_boxes - masks_succeeded

    highest_mask_index = max(analytics[2] for analytics in analytics if analytics[1])
    # Count the number of times each mask index was used.
    mask_usages_by_index = [0] * (highest_mask_index + 1)
    # Count the number of times each mask was perfect.
    perfect_mask_usages_by_index = [0] * (highest_mask_index + 1)
    for analytic in analytics:
        if analytic[1]:
            mask_usages_by_index[analytic[2]] += 1
            if analytic[3] == 0:
                perfect_mask_usages_by_index[analytic[2]] += 1

    # Print the analytics.
    print("\nMask Fitment Analytics")
    print("----------------------")
    print(
        f"Total boxes: {total_boxes} | "
        f"Masks succeeded: {masks_succeeded} ({success_rate}) | "
        f"Masks failed: {clr.Fore.RED}{masks_failed}{clr.Fore.RESET}"
    )
    print(
        f"Perfect masks: {clr.Fore.CYAN}{perfect_masks}{clr.Fore.RESET} ({perfect_mask_rate}) | "
        f"Average border deviation: {average_border_deviation}"
    )
    print("\nMask usage by mask size (smallest to largest):")
    # Make a dict of {index: list contents} for the mask usages, except the last key is "Box mask".
    mask_usages_dict = {
        f"Mask {index}": perfect_total
        for index, perfect_total in enumerate(
            zip(perfect_mask_usages_by_index, mask_usages_by_index)
        )
        if index < len(mask_usages_by_index) - 1
    }
    mask_usages_dict["Box mask"] = perfect_mask_usages_by_index[-1], mask_usages_by_index[-1]

    draw_cleaner_histogram(mask_usages_dict)

    # Find out what pages had how many failures.
    # Structure: {page_path: {"succeeded": 0, "failed": 0}}
    pages_with_success_and_fails_dict: defaultdict[Path, defaultdict[str, int]] = defaultdict(
        lambda: defaultdict(int)
    )
    for analytics in analytics:
        pages_with_success_and_fails_dict[analytics[0]][
            "succeeded" if analytics[1] else "failed"
        ] += 1

    if not pages_with_success_and_fails_dict:
        print("All bubbles were successfully masked.")
        return

    # Flatten the dict into a list of tuples: (page_path, succeeded, failed).
    # Only include pages with at least one failure.
    pages_with_success_and_fails: list[tuple[Path, int, int]] = [
        (page_path, counts["succeeded"], counts["failed"])
        for page_path, counts in pages_with_success_and_fails_dict.items()
        if counts["failed"]
    ]

    # Find and then remove the longest common prefix from the file paths.
    prefix = longest_common_prefix(
        [str(path.parent) for path, _, _ in pages_with_success_and_fails]
    )
    if prefix:
        pages_with_success_and_fails = [
            (path.relative_to(prefix), succeeded, failed)
            for path, succeeded, failed in pages_with_success_and_fails
        ]

    # Sort them list by file path.
    pages_with_success_and_fails = natsorted(pages_with_success_and_fails, key=lambda x: x[0])

    print("\nPages with failures / total:")
    for page_path, succeeded, failed in pages_with_success_and_fails:
        print(f"{page_path}: {clr.Fore.RED}{failed}{clr.Fore.RESET} / {succeeded+failed}")

    print("\n")


def show_denoise_analytics(
    analytics: list[st.DenoiseAnalytic],
    configured_deviation_threshold: float,
    max_deviation_threshold: float,
):
    """
    Present the analytics gathered from the denoising process.

    :param analytics: The analytics gathered from each page, here standard deviations.
    :param configured_deviation_threshold: The configured deviation threshold to de denoising.
    :param max_deviation_threshold: The maximum deviation threshold to discard the mask.
    """
    print("\nDenoising Analytics")
    print("-------------------")

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
    above_ratio = f"{above_threshold_count / total_masks:.0%}" if total_masks else "N/A"

    print(
        f"Total masks: {total_masks} | Masks denoised: {clr.Fore.MAGENTA}{above_threshold_count}{clr.Fore.RESET} "
        f"({above_ratio})"
    )
    print(
        f"Minimum deviation to denoise: {configured_deviation_threshold} | "
        f"Maximum allowed deviation: {max_deviation_threshold}"
    )
    print(f"Standard deviation around masks:\n")

    # Show the lists in a graph.
    draw_denoise_histogram(
        below_threshold,
        above_threshold,
        max_deviation_threshold,
    )
    print("")


def draw_denoise_histogram(
    below_threshold: list[float],
    above_threshold: list[float],
    max_value: float,
):
    """
    Draw a histogram of the deviations.

    :param below_threshold: The standard deviations that were below the threshold.
    :param above_threshold: The standard deviations that were above the threshold.
    :param max_value: The maximum deviation threshold to discard the mask.
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

    width = terminal_width()
    max_label_length = max(len(label) for label, _, _ in buckets_labeled)
    bar_width = width - max_label_length - 16  # 16 is for the spaces and the brackets.

    buckets_labeled = [
        (b_range, int(below * bar_width / max_count), int(above * bar_width / max_count))
        for b_range, below, above in buckets_labeled
    ]

    # Draw the buckets.
    for b_range, below, above in buckets_labeled:
        print(
            f"{b_range} : {'█' * below}{clr.Fore.MAGENTA}{'█' * above} {above}{clr.Fore.RESET} / {below+above}"
        )

    # Draw the legend.
    print(f"\n{clr.Fore.MAGENTA}█ Denoised{clr.Fore.RESET} | █ Total")


def longest_common_prefix(strings: list[str]) -> str:
    """
    Finds the longest common prefix for a list of strings.

    :param strings: The list of strings to find the longest common prefix for.
    :return: The longest common prefix.
    """
    if not strings:
        return ""

    prefix = strings[0]
    for string in strings[1:]:
        while string.find(prefix) != 0:
            prefix = prefix[:-1]
            if not prefix:
                return ""
    return prefix
