import colorsys
from pathlib import Path

import numpy as np
import cv2
import scipy
from PIL import Image, ImageFilter
from logzero import logger

import pcleaner.structures as st
import pcleaner.config as cfg


class BlankMaskError(Exception):
    pass


def convert_mask_to_rgba(mask: Image, color: int | tuple[int, int, int, int] = 255) -> Image:
    """
    Convert "1" mask to "RGBA" mask, where black has an alpha of 0 and white has an alpha of 255.

    :param mask: The mask to convert.
    :param color: [Optional] The color to make the mask, either 1 int (luminance) or 4 ints (rgba).
    :return: The converted mask.
    """
    array_1 = np.array(mask)  # Mode "1" mask.
    color_tuple = (color, color, color, 255) if isinstance(color, int) else color
    # RGBA mask, filled with 0s.
    array_rgba = np.zeros((*array_1.shape, 4), dtype=np.uint8)  # Mode "RGBA" mask.
    # For anything not black in the original mask, set it to (color, color, color, 255).
    array_rgba[array_1 != 0] = color_tuple
    return Image.fromarray(array_rgba)


def apply_debug_filter_to_mask(
    img: Image, color: tuple[int, int, int, int] = (108, 30, 240, 127)
) -> Image:
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


def mask_intersection(mask1: Image, mask2: Image) -> Image:
    """
    Cut out the parts of mask1 that are not in mask2.

    :param mask1: The base mask.
    :param mask2: The mask to cut out of the base mask.
    :return: The intersection mask.
    """
    return Image.composite(mask1, Image.new("1", mask1.size, 0), mask2)


def compose_masks(
    base_size: tuple[int, int], masks_with_pos: list[tuple[Image, tuple[int, int]]]
) -> Image:
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
    base_image: Image, mask_fitments: list[st.MaskFittingResults], output_path: Path
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
    masks = [
        compose_masks(
            base_image.size,
            [
                (mask_fitment.debug_masks[index], mask_fitment.mask_coords)
                for mask_fitment in mask_fitments
            ],
        )
        for index in range(len(mask_fitments[0].debug_masks))
    ]

    # Don't modify the original image.
    base_image = base_image.copy()

    # Generate colors for each mask.
    hues = map(lambda i: (0.15 * i) % 1, range(len(masks)))

    # Convert the hues to RGB tuples and scale the values to the range [0, 255]
    colors = (
        (int(r * 255), int(g * 255), int(b * 255), 255)
        for r, g, b in (colorsys.hsv_to_rgb(hue, 1.0, 1.0) for hue in hues)
    )

    # Make each a different color, then overlay them all on top of each other.
    # Flip the order of the masks, so the largest mask comes first and the rest get pasted on top of it.
    colored_masks = (
        apply_debug_filter_to_mask(mask, color) for mask, color in zip(reversed(masks), colors)
    )

    # Combine the masks.
    combined_mask = Image.new("RGBA", base_image.size)
    for mask in colored_masks:
        combined_mask.paste(mask, (0, 0), mask)

    # Limit the alpha channel to 60% = 153.
    alpha_mask = combined_mask.split()[3]
    alpha_mask = alpha_mask.point(lambda x: min(x, 153))
    base_image.paste(combined_mask, (0, 0), alpha_mask)

    # Save the image.
    base_image.save(output_path)


def make_mask_steps_convolution(mask: Image, growth_step: int = 2, steps: int = 11) -> list[Image]:
    """
    Use convolution to make various sizes of the original mask.
    In each step, the outline of the mask is grown by growth_step pixels.

    :param mask: The mask to make steps of.
    :param growth_step: The amount to grow the mask by each step.
    :param steps: The number of steps to make.
    :return:
    """
    masks = []
    grow_size = growth_step * 2
    mask = mask.convert("L")
    mask_array = np.array(mask, dtype=np.uint8)
    # Make a convolution kernel.
    kernel = np.ones((grow_size + 1, grow_size + 1))
    # Remove the corner pixels from the kernel, this will give 45 degree corners.
    kernel[0, 0] = 0
    kernel[0, -1] = 0
    kernel[-1, 0] = 0
    kernel[-1, -1] = 0
    # Pad the image so that the convolution can handle the edges.
    padded_mask = np.pad(mask_array, ((grow_size, grow_size), (grow_size, grow_size)), mode="edge")

    for _ in range(steps):
        # Apply convolve2d to the image.
        padded_mask = scipy.signal.convolve2d(padded_mask, kernel, mode="same")
        cropped_mask = padded_mask[grow_size:-grow_size, grow_size:-grow_size]
        masks.append(
            Image.fromarray(np.where(cropped_mask > 0, 255, 0).astype(np.uint8)).convert("1")
        )

    # Return them ordered from smallest to largest.
    return masks


def border_std_deviation(base: Image, mask: Image, off_white_threshold: int) -> tuple[float, int]:
    """
    Calculate the border uniformity of a mask.
    For this, find the edge pixels of the mask and then calculate the median color of the pixels around them.
    Also calculate the standard deviation of the colors around the edge pixels.

    In case the mask is blank, return a very high standard deviation.

    :raises BlankMaskError: If one or more masks are blank, meaning that the box is not valid.

    :param base: The base image. Mode: "L"
    :param mask: The mask to calculate the border uniformity of. Mode: "1"
    :param off_white_threshold: The threshold for a pixel to be considered off-white.
    :return: The border uniformity as the standard deviation and the median color of the border.
    """
    # Transform the mask into its edge pixels.
    mask = mask.filter(ImageFilter.FIND_EDGES)
    # Collect all pixels from the base image where the mask has a value of 1.
    # Use numpy for efficiency.
    base_data = np.array(base)
    mask_data = np.array(mask)

    border_pixels = base_data[mask_data == 1]
    # Calculate the number of pixels in the border.
    num_pixels = len(border_pixels)
    if num_pixels == 0:
        # We received an empty mask.
        raise BlankMaskError
    # Calculate the standard deviation of the border pixels.
    std = float(np.std(border_pixels))
    # Get the average color of the border pixels, round to highest integer.
    median_color = int(np.median(border_pixels))
    # logger.debug(f"Border uniformity: {std} ({num_pixels} pixels), median color: {median_color}")
    # Round up any color over the threshold to 255. This should prevent slight off-white colors from sneaking in.
    if median_color > off_white_threshold:
        median_color = 255

    return std, median_color


def cut_out_box(image: Image, box: tuple[int, int, int, int]) -> Image:
    """
    Cut out a box from an image.

    :param image: The image to cut out the box from.
    :param box: The box to cut out.
    :return: The cut out box.
    """
    return image.crop(box)


def cut_out_mask(
    mask: Image,
    box: tuple[int, int, int, int],
    target_shape: tuple[int, int] = None,
    x_padding_offset: int = 0,
    y_padding_offset: int = 0,
) -> Image:
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
    mask = mask.crop(box)
    # If a target shape is given, pad the mask to that shape.
    if target_shape is not None:
        # Create a black image with the target shape.
        padded_mask = Image.new("1", target_shape, 0)
        # Paste the mask into the black image.
        padded_mask.paste(mask, (x_padding_offset, y_padding_offset))
        mask = padded_mask

    return mask


def pick_best_mask(
    base: Image,
    precise_mask: Image,
    box_mask: Image,
    masking_box: tuple[int, int, int, int],
    reference_box: tuple[int, int, int, int],
    cleaner_conf: cfg.CleanerConfig,
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
    :param cleaner_conf: The cleaner config.
    :param analytics_page_path: The path to the original image for the analytics.
    :return: The best mask and what color to make it and the box (along with analytics). If no best
        mask was found, return None for the mask and color.
    """
    # Calculate offset coords between the reference box and the mask box.
    # The mask box was grown by n pixels in each direction to make the reference box,
    # but it could not exceed the image dimensions.
    # These relative coords are used to paste the mask onto the base image.
    x_offset = masking_box[0] - reference_box[0]
    y_offset = masking_box[1] - reference_box[1]

    # Replace all given images with their corresponding cutouts.
    base = cut_out_box(base, reference_box)
    precise_mask = cut_out_mask(precise_mask, masking_box, base.size, x_offset, y_offset)

    # Check that the precise mask is not blank.
    if precise_mask.getbbox() is None:
        # This means the box was probably just noise, so abort picking a mask.
        logger.warning("Found an empty mask, this is likely due to name collisions.")
        return None

    box_mask = cut_out_mask(box_mask, masking_box, base.size, x_offset, y_offset)

    # Generate masks of various sizes for the precise mask, then add the box mask to the list.
    # The generated masks are in ascending size order.
    masks = make_mask_steps_convolution(
        precise_mask, cleaner_conf.mask_growth_step_pixels, cleaner_conf.mask_growth_steps
    )
    masks.append(box_mask)

    # Calculate the border uniformity of each mask.
    # Border deviations: (std deviation, median color)
    border_deviations: list[tuple[Image, int]] = []
    for mask in masks:
        try:
            border_deviations.append(
                border_std_deviation(base, mask, cleaner_conf.off_white_max_threshold)
            )
        except BlankMaskError:
            return None
    # Find the best mask.
    best_mask = None
    lowest_border_deviation = None
    lowest_deviation_color = None
    for i in range(len(masks)):
        if i == 0 or border_deviations[i][0] <= (
            lowest_border_deviation * (1 - cleaner_conf.mask_improvement_threshold)
        ):
            lowest_border_deviation = border_deviations[i][0]
            lowest_deviation_color = border_deviations[i][1]
            best_mask = masks[i]

    # If the std deviation is too high, return None.
    if lowest_border_deviation > cleaner_conf.mask_max_standard_deviation:
        return st.MaskFittingResults(
            best_mask=None,
            median_color=lowest_deviation_color,
            mask_coords=reference_box[:2],
            analytics_page_path=analytics_page_path,
            analytics_mask_index=masks.index(best_mask),
            analytics_std_deviation=lowest_border_deviation,
            mask_box=masking_box,
            debug_masks=masks,
        )
    return st.MaskFittingResults(
        best_mask=best_mask,
        median_color=lowest_deviation_color,
        mask_coords=reference_box[:2],
        analytics_page_path=analytics_page_path,
        analytics_mask_index=masks.index(best_mask),
        analytics_std_deviation=lowest_border_deviation,
        mask_box=masking_box,
        debug_masks=masks,
    )


def combine_best_masks(
    image_size: tuple[int, int], mask_fitments: list[st.MaskFittingResults]
) -> Image:
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
        combined_mask.paste(mask, coords, mask)

    return combined_mask


def combine_noise_masks(
    image_size: tuple[int, int], masks_with_coords: list[tuple[Image, tuple[int, int]]]
) -> Image:
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
        combined_noise_mask.paste(mask, coords)

    return combined_noise_mask


def denoise(
    image: Image,
    colored: bool = False,
    filter_strength: int = 10,
    color_filter_strength: int = 10,
    template_window_size: int = 7,
    search_window_size: int = 21,
) -> Image:
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


def grow_mask(mask: Image, size: int) -> Image:
    """
    Grow the mask by the given amount of pixels.
    Use convolutions to draw a thicker outline.

    :param mask: The mask to grow. Mode: "1"
    :param size: The amount of pixels to grow the mask by.
    :return: The grown mask. Mode: "1"
    """
    grow_size = size * 2
    kernel_size = grow_size + 1
    mask = mask.convert("L")
    mask_array = np.array(mask, dtype=np.uint8)
    # Make a convolution kernel.
    kernel = np.ones((kernel_size, kernel_size), np.uint8)
    # Remove the corner pixels from the kernel, this will give 45 degree corners.
    kernel[0, 0] = 0
    kernel[0, -1] = 0
    kernel[-1, 0] = 0
    kernel[-1, -1] = 0
    # Pad the image so that the convolution can handle the edges.
    padded_mask = np.pad(mask_array, ((grow_size, grow_size), (grow_size, grow_size)), mode="edge")

    # Apply convolve2d to the image.
    padded_mask = scipy.signal.convolve2d(padded_mask, kernel, mode="same")
    cropped_mask = padded_mask[grow_size:-grow_size, grow_size:-grow_size]
    return Image.fromarray(np.where(cropped_mask > 0, 255, 0).astype(np.uint8)).convert("1")


def fade_mask_edges(mask: Image, fade_radius: int) -> Image:
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
    image: Image, mask: Image, box: tuple[int, int, int, int], denoiser_conf: cfg.DenoiserConfig
) -> tuple[Image, tuple[int, int]]:
    """
    Cut out the image and mask using the box, then denoise the image cutout.
    Then grow the mask and fade it's edges.
    Create an alpha composite of the denoised image and the mask.

    :param image: The image to cut out and denoise.
    :param mask: The mask.
    :param box: The box to cut out.
    :param denoiser_conf: The denoiser config.
    :return: The noise mask and it's coordinates.
    """

    # Cut out the image and mask.
    image_cutout = image.crop(box)
    mask_cutout = mask.crop(box)
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

    return denoised_image_cutout, box[:2]
