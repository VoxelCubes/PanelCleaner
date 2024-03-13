import os
from collections import namedtuple
from pathlib import Path

from PIL import Image
from loguru import logger
from simple_lama_inpainting import SimpleLama

import pcleaner.config as cfg
import pcleaner.image_ops as ops
import pcleaner.structures as st
import pcleaner.model_downloader as md


class InpaintingModel:
    def __init__(self, config: cfg.Config) -> None:
        self.model_path = md.get_inpainting_model_path(config)
        # Sanity check: Make sure the model exists.
        if not self.model_path.is_file():
            raise FileNotFoundError(f"Model not found: {self.model_path}")
        # Load the path into the env variable: LAMA_MODEL
        os.environ["LAMA_MODEL"] = str(self.model_path)
        self.simple_lama = SimpleLama()

    def __call__(self, image: Image, mask: Image) -> Image:
        """
        Inpaint the image using the mask.
        The mask must be a 1-channel image where 1 is the area to be inpainted and 0 is the area to keep.

        :param image: Input image.
        :param mask: Mask image.
        :return: The inpainted image.
        """
        # Run the model but ensure the output image is the same size as the input.
        inpainted_image = self.simple_lama(image, mask)
        if inpainted_image.size != image.size:
            width, height = image.size
            inpainted_image = inpainted_image.crop((0, 0, width, height))
        return inpainted_image


def inpaint_page(i_data: st.InpainterData, model: InpaintingModel) -> Image:
    """
    Load the MaskData from the json file and perform the inpainting process.

    :param i_data: All the data needed for the inpainting process.
    :param model: The inpainting model.
    :return: Analytics.
    """
    # Alias.
    g_conf = i_data.general_config
    m_conf = i_data.masker_config
    d_conf = i_data.denoiser_config
    i_conf = i_data.inpainter_config

    # Load all the cached data.
    page_data = st.PageData.from_json(i_data.page_data_json_path.read_text(encoding="utf-8"))
    exact_mask_image = Image.open(page_data.mask_path)
    mask_data = st.MaskData.from_json(i_data.mask_data_json_path.read_text(encoding="utf-8"))
    mask_image = Image.open(mask_data.mask_path)

    original_image = Image.open(mask_data.original_path)
    mask_image_bit = mask_image.convert("1")
    exact_mask_image = exact_mask_image.convert("1")
    original_image = original_image.convert("RGB")
    original_path: Path = mask_data.original_path

    # Clobber protection prefixes have the form "{UUID}_file name", ex. d91d86d1-b8d2-400b-98b2-2d0337973631_0023.json
    clobber_protection_prefix = i_data.page_data_json_path.stem.split("_")[0]
    cache_out_path = (
        i_data.cache_dir
        / f"{clobber_protection_prefix}_{mask_data.original_path.with_suffix('.png').name}"
    )

    def save_mask(img, name_suffix) -> None:
        if i_data.show_masks:
            img.save(cache_out_path.with_stem(cache_out_path.stem + name_suffix))

    # Collect the boxes to inpaint.
    BoxInpaintData = namedtuple("BoxInpaintData", ["box", "image", "deviation"])
    boxes_to_inpaint: list[BoxInpaintData] = []
    analytics_thicknesses: list[int] = []

    # First, find boxes that failed to be masked.
    failed_boxes_deviation: list[tuple[st.Box, float]] = [
        (box, deviation)
        for box, deviation, failed, thickness in mask_data.boxes_with_stats
        if failed
    ]
    # Next, find the boxes meeting the minimum deviation and maximum thickness.
    poorly_fitted_boxes_deviation: list[tuple[st.Box, float]] = [
        (box, deviation)
        for box, deviation, failed, thickness in mask_data.boxes_with_stats
        if not failed
        and deviation >= i_conf.inpainting_min_std_dev
        and thickness
        is not None  # For box masks, this is none. We don't need to inpaint those, they are always good.
        and thickness <= i_conf.min_inpainting_radius
    ]
    # For the failed boxes, synthesize new masks grown to the minimum size.
    # Sample from the exact mask.
    for box, deviation in failed_boxes_deviation:
        mask = ops.cut_out_box(exact_mask_image, box)
        # Grow the mask to the minimum size.
        mask = ops.grow_mask(mask, m_conf.min_mask_thickness)
        boxes_to_inpaint.append(BoxInpaintData(box, mask, deviation))

    for box, deviation in poorly_fitted_boxes_deviation:
        mask = ops.cut_out_box(mask_image_bit, box)
        boxes_to_inpaint.append(BoxInpaintData(box, mask, deviation))

    # Now grow each mask according to the minimum inpainting radius, and the box's deviation.
    padded_boxes_to_inpaint: list[BoxInpaintData] = []
    for box, mask, deviation in boxes_to_inpaint:
        growth = i_conf.min_inpainting_radius
        growth += int(deviation * i_conf.inpainting_radius_multiplier)
        growth = min(growth, i_conf.max_inpainting_radius)
        # The isolation radius is added ahead of time here. We will grow it by this later, but only after
        # the inpainting.
        growth_with_isolation = growth + i_conf.inpainting_isolation_radius
        # Grow the box, then the mask, ensuring it stays within the image bounds.
        box_padded = box.pad(growth_with_isolation, mask_image.size)
        mask_padded = Image.new("1", mask_image.size, 0)
        offset: tuple[int, int] = box.x1 - box_padded.x1, box.y1 - box_padded.y1
        mask_padded.paste(mask, offset)
        mask_padded = ops.grow_mask(mask_padded, growth)
        padded_boxes_to_inpaint.append(BoxInpaintData(box_padded, mask_padded, deviation))
        analytics_thicknesses.append(growth)

    # Merge all the masks into one, then scale it up to the original image size.
    combined_mask = Image.new("1", mask_image.size, 0)
    for box, mask, _ in padded_boxes_to_inpaint:
        combined_mask.paste(mask, (box.x1, box.y1), mask)

    save_mask(combined_mask, "_inpainting_mask")

    # Scale up the masks before inpainting.
    if original_image.size != mask_image.size:
        combined_mask = combined_mask.resize(original_image.size, resample=Image.NEAREST)

    # Inpaint the image.
    if boxes_to_inpaint:
        inpainted_image = model(original_image, combined_mask)
    else:
        inpainted_image = original_image

    # Lastly, grow the masks again by the isolation radius to cut out the inpainted areas.
    isolated_combined_mask = Image.new("1", mask_image.size, 0)
    for box, mask, deviation in padded_boxes_to_inpaint:
        mask = ops.grow_mask(mask, i_conf.inpainting_isolation_radius)
        isolated_combined_mask.paste(mask, (box.x1, box.y1), mask)
    if original_image.size != mask_image.size:
        isolated_combined_mask = isolated_combined_mask.resize(
            original_image.size, resample=Image.NEAREST
        )

    # Apply the mask to the inpainted image.
    inpainted_areas = Image.new("RGBA", original_image.size, 0)
    inpainted_areas.paste(inpainted_image, (0, 0), isolated_combined_mask)

    # Create a new output with these inpainted areas overlayed.
    # But first, apply the cleaning masks.
    cleaned_image = (
        original_image  # Don't bother copying as we won't need this anymore, so overwrite.
    )
    # We need to scale up the mask image to the original image size.
    if original_image.size != mask_image.size:
        mask_image = mask_image.resize(original_image.size, resample=Image.NEAREST)
    cleaned_image.paste(mask_image, (0, 0), mask_image)
    # Then, if denoising was enabled, apply that next.
    expected_noise_mask_path = cache_out_path.with_name(cache_out_path.stem + "_noise_mask.png")
    if d_conf.denoising_enabled and expected_noise_mask_path.is_file():
        noise_mask = Image.open(expected_noise_mask_path)
        cleaned_image.paste(noise_mask, (0, 0), noise_mask)

    cleaned_image.paste(inpainted_areas, (0, 0), isolated_combined_mask)

    # Save output.
    save_mask(inpainted_areas, "_inpainting")
    save_mask(cleaned_image, "_clean_inpaint")

    # Check if the output path is None. In that case we're only outputting to the cache directory.
    if i_data.output_dir is None:
        # Package the analytics. We're only interested in the thicknesses.
        return st.InpaintingAnalytic(tuple(analytics_thicknesses), original_path)

    # Settle on the final output path for the cleaned image.
    if i_data.output_dir.is_absolute():
        final_out_path = i_data.output_dir / mask_data.target_path.name
    else:
        # Take the original image path, and place the image in a subdirectory.
        # This is for when multiple directories were passed in.
        final_out_path = (
            mask_data.target_path.parent / i_data.output_dir / mask_data.target_path.name
        )

    final_out_path.parent.mkdir(parents=True, exist_ok=True)
    final_cleaned_out_path = final_out_path.with_name(final_out_path.stem + "_clean.png")
    final_mask_out_path = final_out_path.with_name(final_out_path.stem + "_mask.png")
    final_mask_inpainted_out_path = final_out_path.with_name(
        final_out_path.stem + "_inpainted_mask.png"
    )

    # Check what the preferred output format is.
    if g_conf.preferred_file_type is None:
        # Use the original file type.
        final_cleaned_out_path = final_cleaned_out_path.with_suffix(original_path.suffix)
    else:
        final_cleaned_out_path = final_cleaned_out_path.with_suffix(g_conf.preferred_file_type)

    if g_conf.preferred_mask_file_type is None:
        # Use png by default.
        final_mask_out_path = final_mask_out_path.with_suffix(".png")
    else:
        final_mask_out_path = final_mask_out_path.with_suffix(g_conf.preferred_mask_file_type)

    # The arg parser should ensure that both can't be true at once, not like that'd be an issue, just plain silly.
    if not i_data.save_only_mask:
        # Save the final image.
        logger.debug(f"Saving final image to {final_cleaned_out_path}")
        ops.save_optimized(cleaned_image, final_cleaned_out_path, original_path)

    if not i_data.save_only_cleaned:
        # Save the final image.
        if i_data.separate_inpaint_masks:
            logger.debug(f"Saving final mask to {final_mask_out_path}")
            ops.save_optimized(mask_image, final_mask_out_path)

            logger.debug(f"Saving final denoised mask to {final_mask_inpainted_out_path}")
            ops.save_optimized(inpainted_areas, final_mask_inpainted_out_path)
        else:
            # Combine both the mask and the denoised mask into one image.
            inpainted_areas.paste(mask_image, (0, 0), mask_image)
            logger.debug(f"Saving final mask to {final_mask_out_path}")
            ops.save_optimized(inpainted_areas, final_mask_out_path)

    if i_data.extract_text:
        # Extract the text layer from the image.
        logger.debug(f"Extracting text from {original_path}")
        base_image = Image.open(original_path)
        text_img = ops.extract_text(base_image, mask_image)
        text_out_path = final_out_path.with_name(final_out_path.stem + "_text.png")
        if g_conf.preferred_mask_file_type is None:
            # Use png by default.
            text_out_path = text_out_path.with_suffix(".png")
        else:
            text_out_path = text_out_path.with_suffix(g_conf.preferred_mask_file_type)
        ops.save_optimized(text_img, text_out_path, original_path)

    # Package the analytics. We're only interested in the thicknesses.
    return st.InpaintingAnalytic(tuple(analytics_thicknesses), original_path)
