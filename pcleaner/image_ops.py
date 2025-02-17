from itertools import cycle
from math import ceil
from pathlib import Path
from importlib import resources
from typing import Generator, Iterable, TypeVar, Any, NewType
from collections import Counter

import cv2
import numpy as np
import colorsys
import scipy
from PIL import Image, ImageFilter, ImageDraw, ImageFont, ImageOps, ImageEnhance
from loguru import logger

import pcleaner.data
import pcleaner.config as cfg
import pcleaner.structures as st
import pcleaner.helpers as hp


class BlankMaskError(Exception):
    pass


def generate_spectrum_colors(n, lightness: float, alpha: int):
    colors = []
    for i in range(n):
        # Sweep from red (0) to purple (270)
        hue = i / n * 300 / 360  # Normalize to range [0, 1]
        # Convert HSL to RGB, then to RGBA
        r, g, b = colorsys.hls_to_rgb(hue, lightness, 1)
        rgba = (int(r * 255), int(g * 255), int(b * 255), alpha)
        colors.append(rgba)
    return colors


def generate_single_color(
    percentage: float, lightness: float, alpha: float
) -> tuple[int, int, int, int]:
    """
    Generate a color based on a percentage of the hue spectrum.

    :param percentage: Hue from red (0.0) to purple (1.0).
    :param lightness: Lightness from black (0.0) to white (1.0).
    :param alpha: Alpha from transparent (0.0) to opaque (1.0).
    :return: The color as an RGBA tuple.
    """
    # Convert the percentage to a position in the hue spectrum (0 to 270 degrees)
    hue = percentage * 265 / 360  # Normalize to range [0, 1]

    # Convert HSL to RGB, then to RGBA
    r, g, b = colorsys.hls_to_rgb(hue, lightness, 1)
    rgba = (int(r * 255), int(g * 255), int(b * 255), int(alpha * 255))
    return rgba


def convert_mask_to_rgba(
    mask: Image.Image,
    color: tuple[int, int, int] | tuple[int, int, int, int] = (255, 255, 255, 255),
) -> Image.Image:
    """
    Convert "1" mask to "RGBA" mask, where black has an alpha of 0 and white has an alpha of 255.

    :param mask: The mask to convert.
    :param color: [Optional] The color to make the mask, either 1 int (luminance) or 4 ints (rgba).
    :return: The converted mask.
    """
    array_1 = np.array(mask)  # Mode "1" mask.
    if len(color) == 3:
        color = (color[0], color[1], color[2], 255)
    # RGBA mask, filled with 0s.
    array_rgba = np.zeros((*array_1.shape, 4), dtype=np.uint8)  # Mode "RGBA" mask.
    # For anything not black in the original mask, set it to (color, color, color, 255).
    array_rgba[array_1 != 0] = color
    return Image.fromarray(array_rgba)


def apply_debug_filter_to_mask(
    img: Image.Image, color: tuple[int, int, int, int] = (108, 30, 240, 127)
) -> Image.Image:
    """
    Make the mask purple and 50% transparent.
    The mask has either transparent or opaque pixels.

    :param img: image to apply the filter to. Mode: "1" or "RGBA"
    :param color: color to make the mask.
    :return: the filtered image. Mode: "RGBA"
    """

    if img.mode == "1":
        return convert_mask_to_rgba(img, color)
    elif img.mode == "RGBA":
        array_rgba = np.array(img)
        array_rgba[array_rgba[:, :, 3] != 0] = color
        return Image.fromarray(array_rgba)
    else:
        raise ValueError(f"Unknown mode: {img.mode}")


def mask_intersection(mask1: Image.Image, mask2: Image.Image) -> Image.Image:
    """
    Cut out the parts of mask1 that are not in mask2.

    :param mask1: The base mask.
    :param mask2: The mask to cut out of the base mask.
    :return: The intersection mask.
    """
    return Image.composite(mask1, Image.new("1", mask1.size, 0), mask2)


def compose_masks(
    base_size: tuple[int, int], masks_with_pos: list[tuple[Image.Image, tuple[int, int]]]
) -> Image.Image:
    """
    Compose a list of masks into one mask.

    :param base_size: The size of the base image.
    :param masks_with_pos: A list of masks and their positions.
    :return: The composed mask.
    """
    # Create a blank mask.
    base_mask = Image.new("1", base_size, 0)

    # Paste each mask onto the base mask.
    for mask, pos in masks_with_pos:
        base_mask.paste(mask, pos, mask)

    return base_mask


def visualize_mask_fitments(
    base_image: Image.Image, mask_fitments: list[st.MaskFittingResults], output_path: Path
) -> None:
    """
    Stack each mask on top of the base image and save the result.
    To make each mask visible, interpolate across a range of colors,
    adding each mask with some opacity.

    :param base_image: The base image to stack the masks on top of.
    :param mask_fitments: The data of the masks to apply.
    :param output_path: The path to save the image to.
    """
    # Compose all masks of the same index into one mask.
    # Each fitment result contains a list of the sub-masks and their positions.
    masks = []
    if mask_fitments:
        max_masks = max(len(mask_fitment.debug_masks) for mask_fitment in mask_fitments)
        for index in range(max_masks):
            mask_list = []
            for mask_fitment in mask_fitments:
                if index >= len(mask_fitment.debug_masks):
                    continue
                mask_tuple = (mask_fitment.debug_masks[index], mask_fitment.mask_coords)
                mask_list.append(mask_tuple)
            mask = compose_masks(base_image.size, mask_list)
            masks.append(mask)
    else:
        logger.warning(f"No masks generated for {output_path.name}")

    # Don't modify the original image.
    base_image = base_image.copy()

    # Convert the hues to RGB tuples and scale the values to the range [0, 255]
    color_tuple = (
        (255, 0, 0, 255),  # Red
        (0, 255, 0, 255),  # Green
        (0, 0, 255, 255),  # Blue
        (255, 0, 255, 255),  # Magenta
        (255, 255, 0, 255),  # Yellow
        (128, 0, 255, 255),  # Purple
        (0, 255, 255, 255),  # Cyan
        (255, 128, 0, 255),  # Orange
    )
    colors = cycle(color_tuple)

    # Make each a different color, then overlay them all on top of each other.
    # Flip the order of the masks, so the largest mask comes first and the rest get pasted on top of it.
    colored_masks = (apply_debug_filter_to_mask(mask, next(colors)) for mask in reversed(masks))

    # Combine the masks.
    combined_mask = Image.new("RGBA", base_image.size)
    for mask in colored_masks:
        mask = mask.convert("RGBA")
        combined_mask.alpha_composite(mask)
    # Limit the alpha channel to 60% = 153.
    alpha_mask = combined_mask.split()[3]
    alpha_mask = alpha_mask.point(lambda x: min(x, 153))
    base_image.paste(combined_mask, (0, 0), alpha_mask)

    # Save the image.
    base_image.save(output_path)


def visualize_standard_deviations(
    base_image: Image.Image,
    mask_fitments: list[st.MaskFittingResults],
    masker_data: cfg.MaskerConfig,
    output_path: Path,
) -> None:
    """
    Draw the chosen mask as well as a box outline and draw the standard deviation
    of the border of the mask.

    :param base_image: The base image to stack the masks on top of.
    :param mask_fitments: The data of the masks to apply.
    :param masker_data: The masker config.
    :param output_path: The path to save the image to.
    """

    text_offset_x: int = 5
    text_offset_y: int = 4

    # Don't modify the original image.
    base_image = base_image.copy()

    font_path = hp.resource_path(pcleaner.data, "LiberationSans-Regular.ttf")
    logger.debug(f"Loading included font from {font_path}")
    # Figure out the optimal font size based on the image size. E.g. 30 for a 1600px image.
    font_size = int(base_image.size[0] / 50) + 5
    font = ImageFont.truetype(font_path, font_size)

    step_thickness = masker_data.mask_growth_step_pixels
    max_standard_deviation = masker_data.mask_max_standard_deviation

    # For each fitment, draw the mask if one was chosen, coloring it according to the index.
    # Also draw the bounding box in green, but choose red if no mask was chosen.
    # Finally, draw the mask's standard deviation in the top left corner (or the max deviation if none was chosen),
    # with the thickness of the outline under that, calculated as the mask index * growth per step (if applicable).
    for fitment in mask_fitments:
        fitment: st.MaskFittingResults
        text_x = fitment.mask_box.x1
        text_y = fitment.mask_box.y1
        if fitment.best_mask is not None:
            # Draw the mask.
            mask = fitment.best_mask
            # color = colors[fitment.analytics_mask_index]
            # Base the color off of the std deviation in relation to the max std deviation.
            color_offset = (1 - fitment.analytics_std_deviation / max_standard_deviation) ** 4
            color = generate_single_color(color_offset, 0.5, 0.7)
            mask = apply_debug_filter_to_mask(mask, color)
            base_image.paste(mask, fitment.mask_coords, mask)

            # Draw the border standard deviation.
            std_deviation = fitment.analytics_std_deviation
            thickness = fitment.analytics_thickness
            # Draw the standard deviation, use \sigma for the symbol.
            text = f"\u03C3={std_deviation:.2f}"
            draw = ImageDraw.Draw(base_image)
            draw.rectangle(fitment.mask_box.as_tuple, outline=(0, 255, 0, 255), width=3)
            draw.text(
                (text_x + text_offset_x, text_y + text_offset_y),
                text,
                font=font,
                fill="black",
                stroke_width=3,
                stroke_fill="white",
            )
            if thickness is not None:
                text = f"{thickness}px"
                draw.text(
                    (text_x + text_offset_x, text_y + text_offset_y + font_size + 2),
                    text,
                    font=font,
                    fill="black",
                    stroke_width=3,
                    stroke_fill="white",
                )
        else:
            # Draw the bounding box and a big ol cross going through it.
            draw = ImageDraw.Draw(base_image)
            draw.line(
                (
                    fitment.mask_box.x1 + 1,
                    fitment.mask_box.y1 + 1,
                    fitment.mask_box.x2 - 1,
                    fitment.mask_box.y2 - 1,
                ),
                fill=(255, 0, 0, 255),
                width=3,
            )
            draw.line(
                (
                    fitment.mask_box.x1 + 1,
                    fitment.mask_box.y2 - 1,
                    fitment.mask_box.x2 - 1,
                    fitment.mask_box.y1 + 1,
                ),
                fill=(255, 0, 0, 255),
                width=3,
            )
            draw.rectangle(fitment.mask_box.as_tuple, outline=(255, 0, 0, 255), width=3)
            std_deviation = fitment.analytics_std_deviation
            text = f"\u03C3={std_deviation:.2f}"
            draw.text(
                (text_x + text_offset_x, text_y + text_offset_y),
                text,
                font=font,
                fill="#900",
                stroke_width=3,
                stroke_fill="white",
            )

    # Save the image.
    base_image.save(output_path)


def make_growth_kernel(thickness: int) -> np.ndarray:
    """
    Make a growth kernel to add an outline of the given thickness.
    Round the corners for a small mask, or create a proper ellipse for a larger mask.

    :param thickness: The thickness of the outline.
    :return: The growth kernel. Size: (thickness * 2 + 1, thickness * 2 + 1)
    """

    diameter = thickness * 2 + 1

    if diameter <= 5:
        # Round off the corners for a small mask.
        kernel = np.ones((diameter, diameter), dtype=np.float64)
        kernel[0, 0] = 0
        kernel[0, -1] = 0
        kernel[-1, 0] = 0
        kernel[-1, -1] = 0
    else:
        # Create a proper ellipse for a larger mask.
        kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (diameter, diameter))
        # Convert to float64 for the convolution.
        kernel = kernel.astype(np.float64)

    return kernel


def make_mask_steps_convolution(
    mask: Image.Image, growth_step: int, steps: int, min_thickness: int
) -> Generator[tuple[Image.Image, int | None], None, None]:
    """
    Use convolution to make various sizes of the original mask.
    In each step, the outline of the mask is grown by growth_step pixels.

    :param mask: The mask to make steps of.
    :param growth_step: The amount to grow the mask by each step.
    :param steps: The number of steps to make.
    :param min_thickness: The minimum thickness of the mask. Used as the first step.
    :return: A generator of the masks with their thickness.
    """
    # This padding is for the convolution kernel sweeping across the pixels.
    # It needs half the growth size on each side for context, otherwise the edge will be wonky.
    padding_for_kernel = max(min_thickness, growth_step) * 2
    mask = mask.convert("L")
    mask_array = np.array(mask, dtype=np.uint8)
    # Make a convolution kernel.
    kernel = make_growth_kernel(growth_step)
    kernel_first = make_growth_kernel(min_thickness)

    # Pad the image so that the convolution can handle the edges.
    padded_mask = np.pad(
        mask_array,
        ((padding_for_kernel, padding_for_kernel), (padding_for_kernel, padding_for_kernel)),
        mode="edge",
    )
    # Apply convolve2d to the image.
    padded_mask = scipy.signal.convolve2d(padded_mask, kernel_first, mode="same")
    # Remove the extended edges from the padding.
    cropped_mask = padded_mask[
        padding_for_kernel:-padding_for_kernel, padding_for_kernel:-padding_for_kernel
    ]
    yield Image.fromarray(np.where(cropped_mask > 0, 255, 0).astype(np.uint8)).convert(
        "1"
    ), min_thickness

    for index in range(steps - 1):
        # Apply convolve2d to the image.
        padded_mask = scipy.signal.convolve2d(padded_mask, kernel, mode="same")
        cropped_mask = padded_mask[
            padding_for_kernel:-padding_for_kernel, padding_for_kernel:-padding_for_kernel
        ]
        yield Image.fromarray(np.where(cropped_mask > 0, 255, 0).astype(np.uint8)).convert(
            "1"
        ), min_thickness + (index + 1) * growth_step


def heuristic_median_color(colors: np.ndarray) -> np.ndarray | None:
    """
    Check if any color occurs in more than 50% of the rows as a
    simple check for the median.

    :param colors: ndarray of shape (n_samples, 3), where each row is an RGB color.
    :return: The median color, if found.
    """
    # Convert each RGB color to a tuple for hashing in Counter
    color_tuples = [tuple(color) for color in colors]

    color_counts = Counter(color_tuples)
    total_colors = len(colors)

    # Check if any color occurs more than 50% of the time
    for color, count in color_counts.items():
        if count > total_colors / 2:
            median_color = np.array(color)
            return median_color

    return None


def geometric_median(points: np.ndarray, epsilon=1e-5, max_iterations=500) -> np.ndarray:
    """
    Compute the geometric median of a set of points using Weiszfeld's algorithm.

    :param points: ndarray of shape (n_samples, n_dimensions), the input points.
    :param epsilon: float, the convergence tolerance.
    :param max_iterations: int, the maximum number of iterations.
    :return: ndarray of shape (n_dimensions,), the computed geometric median.
    """
    # Initial estimate: mean of the points
    median = np.mean(points, axis=0)

    for iteration in range(max_iterations):
        # Compute distances from the current median to all points
        distances = np.linalg.norm(points - median, axis=1)

        # Identify points not exactly at the median to avoid division by zero
        non_zero_distances = distances > 0

        if not np.any(non_zero_distances):
            # All points are at the current median
            return median

        # Weights are inversely proportional to distances
        inverse_distances = 1 / distances[non_zero_distances]
        total_inverse_distance = np.sum(inverse_distances)
        weights = inverse_distances / total_inverse_distance

        # Update the median estimate
        new_median = np.sum(weights[:, np.newaxis] * points[non_zero_distances], axis=0)

        # Check for convergence
        median_shift = np.linalg.norm(new_median - median)
        if median_shift < epsilon:
            return new_median

        median = new_median

    # Return the last estimate if convergence was not reached
    return median


def color_std(colors: np.ndarray) -> float:
    """
    Compute the standard deviation of colors based on Euclidean distances
    from each color to the mean color.

    :param colors: ndarray of shape (n_samples, 3), where each row is an RGB color.
    :returns: the standard deviation of the colors.
    """
    # Ensure colors are in floating-point for accurate calculations
    colors = colors.astype(np.float64)
    mean_color = np.mean(colors, axis=0)
    # Compute distances from each color to the mean color
    distances = np.linalg.norm(colors - mean_color, axis=1)

    # Compute the standard deviation of the distances
    std_dev = np.std(distances, ddof=1)  # Using sample standard deviation (ddof=1)
    return std_dev


def border_std_deviation(
    base: Image.Image, mask: Image.Image, off_white_threshold: int, allow_color: bool
) -> tuple[float, tuple[int, int, int]]:
    """
    Calculate the border uniformity of a mask.
    For this, find the edge pixels of the mask and then calculate the median color of the pixels around them.
    Also calculate the standard deviation of the colors around the edge pixels.

    In case the mask is blank, return a very high standard deviation.

    :raises BlankMaskError: If one or more masks are blank, meaning that the box is not valid.

    :param base: The base image. Mode: "L"
    :param mask: The mask to calculate the border uniformity of. Mode: "1"
    :param off_white_threshold: The threshold for a pixel to be considered off-white.
    :param allow_color: Whether to allow colored masks.
    :return: The border uniformity as the standard deviation and the median color of the border.
    """
    if not allow_color:
        # Convert the base image to grayscale.
        base = base.convert("L")
    # Transform the mask into its edge pixels.
    mask = mask.filter(ImageFilter.FIND_EDGES)
    # Collect all pixels from the base image where the mask has a value of 1.
    base_data = np.array(base)
    mask_data = np.array(mask)

    border_pixels = base_data[mask_data == 1]
    # Calculate the number of pixels in the border.
    num_pixels = len(border_pixels)
    if num_pixels == 0:
        # We received an empty mask.
        raise BlankMaskError

    # Calculate the standard deviation of the border pixels.
    # Get the average color of the border pixels, round to highest integer.
    # Check if we're dealing with L or RGB columns in the border pixels.
    if len(border_pixels.shape) == 1:
        # We're dealing with a grayscale image.
        std = float(np.std(border_pixels))
        median_color = int(np.median(border_pixels))
        median_color = (median_color, median_color, median_color)
    else:
        # We're dealing with an RGB image.
        std = color_std(border_pixels)
        median_color = heuristic_median_color(border_pixels)
        if median_color is None:
            median_color = geometric_median(border_pixels)
        median_color = tuple(int(color) for color in median_color)

    # logger.debug(f"Border uniformity: {std} ({num_pixels} pixels), median color: {median_color}")
    # Round up any color over the threshold to 255. This should prevent slight off-white colors from sneaking in.
    if min(median_color) > off_white_threshold:
        median_color = (255, 255, 255)

    return std, median_color


def cut_out_box(image: Image.Image, box: st.Box) -> Image.Image:
    """
    Cut out a box from an image.

    :param image: The image to cut out the box from.
    :param box: The box to cut out.
    :return: The cut out box.
    """
    return image.crop(box.as_tuple)


def cut_out_mask(
    mask: Image.Image,
    box: st.Box,
    target_shape: tuple[int, int] = None,
    x_padding_offset: int = 0,
    y_padding_offset: int = 0,
) -> Image.Image:
    """
    Cut out a box from a mask.
    If a target shape is given, the mask is padded to that shape with black.
    Use the offset to move the mask to the correct position when padding.

    :param mask: Mask image in mode "1".
    :param box: The box to cut out.
    :param target_shape: [Optional] The target shape to pad the mask to.
    :param x_padding_offset: [Optional] The x offset of the mask when padding.
    :param y_padding_offset: [Optional] The y offset of the mask when padding.
    :return: The cut out mask.
    """
    # Cut out the box.
    mask = mask.crop(box.as_tuple)
    # If a target shape is given, pad the mask to that shape.
    if target_shape is not None:
        # Create a black image with the target shape.
        padded_mask = Image.new("1", target_shape, 0)
        # Paste the mask into the black image.
        padded_mask.paste(mask, (x_padding_offset, y_padding_offset))
        mask = padded_mask

    return mask


def pick_best_mask(
    base: Image.Image,
    precise_mask: Image.Image,
    box_mask: Image.Image,
    masking_box: st.Box,
    reference_box: st.Box,
    masker_conf: cfg.MaskerConfig,
    analytics_page_path: Path,
) -> None | st.MaskFittingResults:
    """
    Generate various sizes of the precise mask and pick the best one from
    among them, and the box mask.

    Return the best mask, the median color of the border, and the coordinates of the mask.
    If the best standard deviation is too high, return None for the mask and color.

    If the precise mask is blank, return None. This happens when the AI picked up some noise.

    "Best" is defined as having the lowest std deviation at the greatest mask size.
    Here, the standard deviation among the color of pixels along the edge of the mask is calculated.
    If they're all the same color, we can safely assume that the mask is a good fit.

    It also returns analytics, containing the standard deviation of the best mask and its index.
    These can be used to gauge how good the mask generation was.


    :param base: The base image.
    :param precise_mask: The precise mask.
    :param box_mask: The box mask.
    :param masking_box: The box to cut the mask out of.
    :param reference_box: The box to cut the base image out of.
    :param masker_conf: The masker config.
    :param analytics_page_path: The path to the original image for the analytics.
    :return: The best mask and what color to make it and the box (along with analytics). If no best
        mask was found, return None for the mask and color.
    """
    # Calculate offset coords between the reference box and the mask box.
    # The mask box was grown by n pixels in each direction to make the reference box,
    # but it could not exceed the image dimensions.
    # These relative coords are used to paste the mask onto the base image.
    x_offset = masking_box.x1 - reference_box.x1
    y_offset = masking_box.y1 - reference_box.y1

    # Replace all given images with their corresponding cutouts.
    base = cut_out_box(base, reference_box)
    precise_mask_cut = cut_out_mask(precise_mask, masking_box, base.size, x_offset, y_offset)

    # Check that the precise mask is not blank.
    if precise_mask_cut.getbbox() is None:
        # This means the box was probably just noise, so abort picking a mask.
        logger.warning(
            "Found an empty mask, the Text Detector didn't find anything but still recorded text present.\n"
            f"Image: {analytics_page_path.name} Masking box: {masking_box}, x offset: {x_offset}, y offset: {y_offset}."
            f" Skipping."
        )
        return None

    box_mask = cut_out_mask(box_mask, masking_box, base.size, x_offset, y_offset)
    # Thickness doesn't really apply to the box mask, as it isn't grown from the precise mask.
    box_mask_with_thickness: tuple[Image.Image, int | None] = (box_mask, None)

    # Generate masks of various sizes for the precise mask, then add the box mask to the list.
    # The generated masks are in ascending size order.
    mask_gen = make_mask_steps_convolution(
        precise_mask_cut,
        masker_conf.mask_growth_step_pixels,
        masker_conf.mask_growth_steps,
        masker_conf.min_mask_thickness,
    )

    # When using the fast mask selection, make a new generator with the box mask as the first mask,
    # followed by the generated masks.
    T = TypeVar("T")

    def generator_with_first(generator: Iterable[T], first: T) -> Generator[T, None, None]:
        yield first
        yield from generator

    def generator_with_last(generator: Iterable[T], last: T) -> Generator[T, None, None]:
        yield from generator
        yield last

    if masker_conf.mask_selection_fast:
        mask_stream = generator_with_first(mask_gen, box_mask_with_thickness)
    else:
        mask_stream = generator_with_last(mask_gen, box_mask_with_thickness)

    # Calculate the border uniformity of each mask.
    # Border deviations: (std deviation, median color)
    border_deviations: list[tuple[float, tuple[int, int, int]]] = []
    masks = []
    thicknesses = []
    for mask, thickness in mask_stream:
        try:
            masks.append(mask)
            thicknesses.append(thickness)
            current_deviation = border_std_deviation(
                base, mask, masker_conf.off_white_max_threshold, masker_conf.allow_colored_masks
            )
            border_deviations.append(current_deviation)
            # Break on the first perfect mask if using the fast mask selection.
            if masker_conf.mask_selection_fast and current_deviation[0] == 0:
                break
        except BlankMaskError:
            return None
    # Find the best mask.
    best_mask = None
    lowest_border_deviation = None
    lowest_deviation_color: int | tuple[int, int, int] | None = None
    chosen_thickness = None
    for i, border_deviation in enumerate(border_deviations):
        mask_deviation, mask_color = border_deviation
        if i == 0 or mask_deviation <= (
            lowest_border_deviation * (1 - masker_conf.mask_improvement_threshold)
        ):
            lowest_border_deviation = mask_deviation
            lowest_deviation_color = mask_color
            best_mask = masks[i]
            chosen_thickness = thicknesses[i]

    # If the std deviation is too high, return None.
    if lowest_border_deviation > masker_conf.mask_max_standard_deviation:
        return st.MaskFittingResults(
            best_mask=None,
            median_color=lowest_deviation_color,
            mask_coords=(reference_box.x1, reference_box.y1),
            analytics_page_path=analytics_page_path,
            analytics_mask_index=masks.index(best_mask),
            analytics_std_deviation=lowest_border_deviation,
            analytics_thickness=chosen_thickness,
            mask_box=masking_box,
            debug_masks=masks,
        )
    return st.MaskFittingResults(
        best_mask=best_mask,
        median_color=lowest_deviation_color,
        mask_coords=(reference_box.x1, reference_box.y1),
        analytics_page_path=analytics_page_path,
        analytics_mask_index=masks.index(best_mask),
        analytics_std_deviation=lowest_border_deviation,
        analytics_thickness=chosen_thickness,
        mask_box=masking_box,
        debug_masks=masks,
    )


def combine_best_masks(
    image_size: tuple[int, int], mask_fitments: Iterable[st.MaskFittingResults]
) -> Image.Image:
    """
    Merge the masks together into a single mask in RGBA mode to preserve the black/white information.
    Masks are in mode "1".

    :param image_size: The size of the image to make the mask for.
    :param mask_fitments: The data of the masks to apply.
    :return: The combined mask. Image mode: "RGBA"
    """
    combined_mask = Image.new("RGBA", image_size, (0, 0, 0, 0))
    # Convert the masks to RGBA mode.
    # Then paste the mask onto the combined mask.
    for mask_fitment in mask_fitments:
        mask, color, coords = mask_fitment.mask_data
        mask = convert_mask_to_rgba(mask, color)
        combined_mask.alpha_composite(mask, coords)

    return combined_mask


def combine_noise_masks(
    image_size: tuple[int, int], masks_with_coords: list[tuple[Image.Image, tuple[int, int]]]
) -> Image.Image:
    """
    Merge the noise masks together into a single mask in RGBA mode.
    The noise mask may be blank if all masks either failed or fitted too well.

    :param image_size: The size of the image to make the mask for.
    :param masks_with_coords: The masks to combine with their coordinates.
    :return: The combined mask. Image mode: "RGBA" and whether the mask is blank.
    """
    combined_noise_mask = Image.new("RGBA", image_size, (0, 0, 0, 0))
    # Then paste the mask onto the combined mask.
    for mask, coords in masks_with_coords:
        # Ensure both images are RGBA to safely alpha composite them.
        mask = mask.convert("RGBA")
        combined_noise_mask.alpha_composite(mask, coords)

    return combined_noise_mask


def denoise(
    image: Image.Image,
    colored: bool = False,
    filter_strength: int = 10,
    color_filter_strength: int = 10,
    template_window_size: int = 7,
    search_window_size: int = 21,
) -> Image.Image:
    """
    Denoise the image using cv2.

    :param image: The image to denoise.
    :param colored: Whether the image is colored or not, to use the appropriate algorithm.
    :param filter_strength: The strength of the filter. Higher values mean more denoising.
    :param color_filter_strength: The strength of the color filter. Higher values mean more denoising.
    :param template_window_size: Size in pixels of the template patch that is used to compute weights. Should be odd.
    :param search_window_size: Size in pixels of the window that is used to compute weighted average for given pixel. Should be odd.
    :return: The denoised image.
    """
    if colored:
        return Image.fromarray(
            cv2.fastNlMeansDenoisingColored(
                np.array(image),
                None,
                filter_strength,
                color_filter_strength,
                template_window_size,
                search_window_size,
            )
        )
    else:
        return Image.fromarray(
            cv2.fastNlMeansDenoising(
                np.array(image), None, filter_strength, template_window_size, search_window_size
            )
        )


def grow_mask(mask: Image.Image, size: int) -> Image.Image:
    """
    Grow the mask by the given amount of pixels.
    Use convolutions to draw a thicker outline.

    :param mask: The mask to grow. Mode: "1"
    :param size: The amount of pixels to grow the mask by.
    :return: The grown mask. Mode: "1"
    """
    if size == 0:
        return mask
    grow_size = size * 2
    mask = mask.convert("L")
    mask_array = np.array(mask, dtype=np.uint8)
    # Make a convolution kernel.
    kernel = make_growth_kernel(size)
    # Pad the image so that the convolution can handle the edges.
    padded_mask = np.pad(mask_array, ((grow_size, grow_size), (grow_size, grow_size)), mode="edge")

    # Apply convolve2d to the image.
    padded_mask = scipy.signal.convolve2d(padded_mask, kernel, mode="same")
    cropped_mask = padded_mask[grow_size:-grow_size, grow_size:-grow_size]
    return Image.fromarray(np.where(cropped_mask > 0, 255, 0).astype(np.uint8)).convert("1")


def fade_mask_edges(mask: Image.Image, fade_radius: int) -> Image.Image:
    """
    Fade the edges of the mask by the given amount of pixels.

    :param mask: mask to fade. Mode: "1"
    :param fade_radius: The amount of pixels to fade the mask by.
    :return: The faded mask. Mode: "L"
    """
    # Use gaussian blur to fade the edges, perform it in L mode.
    mask = mask.convert("L").filter(ImageFilter.GaussianBlur(fade_radius))
    return mask


def generate_noise_mask(
    image: Image.Image,
    mask: Image.Image,
    box: st.Box,
    denoiser_conf: cfg.DenoiserConfig,
    scale_factor: float,
) -> tuple[Image.Image, tuple[int, int]]:
    """
    Cut out the image and mask using the box, then denoise the image cutout.
    Then grow the mask and fade it's edges.
    Create an alpha composite of the denoised image and the mask.
    For the scale factor, a factor of 2 means that the original image is twice the size of the mask,
    so we need to scale up box coordinates by 2.

    :param image: The image to cut out and denoise.
    :param mask: The mask.
    :param box: The box to cut out.
    :param denoiser_conf: The denoiser config.
    :param scale_factor: The scale factor of the image, how much to scale the box coordinates by.
    :return: The noise mask and it's coordinates (using the top left).
    """
    # Scale the box coordinates.
    box = box.scale(scale_factor)

    # Cut out the image and mask.
    image_cutout = image.crop(box.as_tuple)
    mask_cutout = mask.crop(box.as_tuple)
    mask_cutout = grow_mask(mask_cutout, denoiser_conf.noise_outline_size)
    mask_faded = fade_mask_edges(mask_cutout, denoiser_conf.noise_fade_radius)

    # Denoise the image cutout.
    denoised_image_cutout = denoise(
        image_cutout,
        denoiser_conf.colored_images,
        denoiser_conf.filter_strength,
        denoiser_conf.color_filter_strength,
        denoiser_conf.template_window_size,
        denoiser_conf.search_window_size,
    )

    # Add alpha channels.
    denoised_image_cutout.putalpha(mask_faded)

    return denoised_image_cutout, (box.x1, box.y1)


def extract_text(base_image: Image.Image, mask: Image.Image) -> Image.Image:
    """
    Extract the text from the base image using the combined mask.
    This essentially deletes everything but the text from the image,
    the inverse of the mask.

    Before extracting the text, the mask must be resized to the base image size,
    if it isn't already.

    :param base_image: The base image.
    :param mask: The mask of the text. Mode: "1"
    :return: The image with only the text.
    """
    # Create a blank canvas.
    text_image = Image.new("RGBA", base_image.size, (0, 0, 0, 0))
    # Resize the mask to the base image size.
    if mask.size != base_image.size:
        mask = mask.resize(base_image.size, Image.NEAREST)
    # Paste the base image onto the canvas using the mask.
    text_image.paste(base_image, (0, 0), mask)
    return text_image


def pad_image(
    image: Image.Image,
    padding: int | tuple[int, int, int, int],
    fill_color: tuple[int, int, int] = (255, 255, 255),
) -> Image.Image:
    """
    Pads an image with the specified padding and fill color.

    :param image: the image to pad.
    :param padding: Padding size in pixels. This can be a single integer or a tuple of four integers.
    :param fill_color: The color to use for the padding. Default is white.
    :return: A new PIL Image object with the padding applied.
    """
    padded_image = ImageOps.expand(image, border=padding, fill=fill_color)
    return padded_image


def visualize_raw_boxes(
    image: np.ndarray, raw_boxes: list[dict[str, Any]], output_path: Path
) -> None:
    """
    Create a debug visualization of the raw boxes detected in the image.

    :param image: The image to visualize the raw boxes on.
    :param raw_boxes: The raw boxes to visualize.
    :param output_path: The path to save the visualization to.
    """
    # Fix flipped R and B channels.
    image = Image.fromarray(image[:, :, ::-1])

    font_path = hp.resource_path(pcleaner.data, "LiberationSans-Regular.ttf")
    logger.debug(f"Loading included font from {font_path}")
    # Figure out the optimal font size based on the image size. E.g. 30 for a 1600px image.
    font_size = int(image.size[0] / 50) + 5

    # Fill layer for box background.
    # Just giving the fill an alpha value didn't work, I tried.
    fill_layer = Image.new("RGBA", image.size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(fill_layer)
    for index, box_data in enumerate(raw_boxes):
        # This is a list of x1, y1, x2, y2.
        box_xyxy: tuple[int, int, int, int] = box_data["xyxy"]

        # Draw a transparent rectangle fill as the base.
        draw.rectangle(box_xyxy, fill="green")

    # Paste the fill layer onto the image.
    FILL_ALPHA = 48
    alpha = fill_layer.split()[3]
    alpha = ImageEnhance.Brightness(alpha).enhance(FILL_ALPHA / 255)
    fill_layer.putalpha(alpha)

    # Composite the fill layer onto the original image
    image = Image.alpha_composite(image.convert("RGBA"), fill_layer)
    draw = ImageDraw.Draw(image)

    for index, box_data in enumerate(raw_boxes):
        # Parse out the bounding box, boxes of the lines, and the language.
        # This is a list of x1, y1, x2, y2.
        box_xyxy: tuple[int, int, int, int] = box_data["xyxy"]
        # The lines are stored as a list of all 4 corner points.
        Point = NewType("Point", tuple[int, int])
        lines: list[tuple[Point, Point, Point, Point]] = box_data["lines"]
        # The supposed language of the text.
        language: str = box_data["language"]

        for line in lines:
            # Draw the lines between the points.
            for i in range(4):
                x1, y1 = line[i]
                x2, y2 = line[(i + 1) % 4]
                draw.line((x1, y1, x2, y2), fill="cyan", width=2)

        draw.rectangle(box_xyxy, outline="green")

        # Draw the box number, with a white background, respecting font size.
        draw.text(
            (box_xyxy[0] + 4, box_xyxy[1]),
            str(index + 1),
            fill="green",
            font=ImageFont.truetype(font_path, font_size),
            stroke_fill="white",
            stroke_width=3,
        )
        draw.text(
            (box_xyxy[0] + 4, box_xyxy[1] + font_size + 2),
            language,
            fill="purple",
            font=ImageFont.truetype(font_path, font_size),
            stroke_fill="white",
            stroke_width=3,
        )

    image.save(output_path)


def calculate_best_splits(
    image_path: Path | str,
    preferred_height: int,
    tolerance: int,
    split_strips: bool,
    max_aspect_ratio: float,
) -> list[int]:
    """
    Check if we should split the image into smaller vertical segments.
    We check for good splits by comparing the change in pixels horizontally.
    We then pick the best one in the preferred height range.

    :param image_path: The path to the image to calculate the best splits for.
    :param preferred_height: The preferred height of the strips.
    :param tolerance: The pixel range to consider for the preferred height.
    :param split_strips: Whether to even split the strips or not.
    :param max_aspect_ratio: The maximum aspect ratio of the strips to consider splitting.
    :return: A list of y values to split the image at.
    """
    if not split_strips:
        return []

    image = Image.open(image_path)
    width, height = image.size

    if height <= preferred_height:
        return []

    if width / height > max_aspect_ratio:
        return []

    # Calculate the number of strips to split the image into.
    # We want to avoid leaving a tiny strip at the end.
    num_strips = ceil(height / preferred_height) - 1
    preferred_height = height // (num_strips + 1)
    splits = [preferred_height * i for i in range(1, num_strips + 1)]
    # Adjust the tolerance to prevent overlapping search ranges
    # and invalid search ranges near the image edges.
    tolerance = min(tolerance, preferred_height // 2)

    if tolerance == 0:
        return splits

    # Perform the calculation on the luminance alone,
    # as human vision is more sensitive to changes in luminance than color,
    # an important feature in the image will be unlikely to lack contrast
    # in this channel.
    image_luminance = image.convert("L")
    luminance = np.array(image_luminance)

    # Search for the minimum changes for each split's range.
    for index, split in enumerate(splits):
        search_start = split - tolerance
        search_end = split + tolerance

        search_range = luminance[search_start:search_end, :]
        # We want to penalize large changes more than small changes,
        # so we square the differences.
        # Even if the pixel changed by 255 each time, we would need a width of 2^14 to overflow.
        horizontal_changes = np.sum(np.square(np.diff(search_range, axis=1)), axis=1)

        # Create a bitmap by thresholding the horizontal changes using the 10th percentile.
        # This way we can still optimize the exact split location when the image is noisy.
        threshold = np.percentile(horizontal_changes, 10)
        horizontal_changes_bitmap = (horizontal_changes > threshold).astype(np.uint8)

        # Find the optimal region by identifying the center of the region with the lowest values
        small_value_indices = np.where(horizontal_changes_bitmap == 0)[0]

        if len(small_value_indices) > 0:
            diff_indices = np.diff(small_value_indices)
            split_points = np.where(diff_indices > 1)[0]
            split_points = np.concatenate(([0], split_points + 1, [len(small_value_indices)]))

            best_region_length = 0
            best_region_start = 0
            for i in range(len(split_points) - 1):
                start = split_points[i]
                end = split_points[i + 1]
                current_length = end - start
                if current_length > best_region_length:
                    best_region_length = current_length
                    best_region_start = start

            # Set the best split to the center of the largest contiguous region of small values
            best_split = small_value_indices[best_region_start + (best_region_length // 2)]
        else:
            # Fallback to the row with the minimum value if no region found
            best_split = np.argmin(horizontal_changes)

        splits[index] = search_start + best_split

    return splits


def split_image(image_path: Path | str, splits: list[int]) -> list[Image.Image]:
    """
    Split the image into multiple strips at the given y coordinates.

    :param image_path: The path to the image to split.
    :param splits: The y coordinates to split the image at.
    :return: A list of the split images.
    """
    image = Image.open(image_path)
    split_images = []
    y1 = 0
    for y2 in splits:
        split_images.append(image.crop((0, y1, image.width, y2)))
        y1 = y2
    split_images.append(image.crop((0, y1, image.width, image.height)))
    return split_images


def stitch_images(image_paths: list[Path], output_path: Path) -> None:
    """
    Stitch the images together vertically.

    :param image_paths: The paths to the images to stitch.
    :param output_path: The path to save the stitched image to.
    """
    images = [Image.open(image_path) for image_path in image_paths]
    widths, heights = zip(*(i.size for i in images))

    total_width = max(widths)
    total_height = sum(heights)

    def get_greatest_common_mode(modes: list[str]) -> str:
        # Define a hierarchy for image modes
        mode_hierarchy = ["1", "L", "P", "LA", "RGB", "RGBA", "CMYK", "YCbCr"]

        # Get the highest-ranked mode from the list
        greatest_mode = max(modes, key=lambda mode: mode_hierarchy.index(mode))

        return greatest_mode

    # Get greatest common mode for the images.
    image_modes = [image.mode for image in images]
    stitched_image = Image.new(get_greatest_common_mode(image_modes), (total_width, total_height))

    y_offset = 0
    for image in images:
        stitched_image.paste(image, (0, y_offset))
        y_offset += image.size[1]

    stitched_image.save(output_path)
