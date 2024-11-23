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
import pcleaner.output_structures as ost


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

    path_gen = ost.OutputPathGenerator(original_path, i_data.cache_dir, i_data.page_data_json_path)

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

    # Create a new output with these inpainted areas overlayed.
    # But first, apply the cleaning masks.
    # Don't bother copying as we won't need this anymore, so overwrite.
    cleaned_image = original_image.convert("RGBA")
    # We need to scale up the mask image to the original image size.
    if original_image.size != mask_image.size:
        mask_image = mask_image.resize(original_image.size, resample=Image.NEAREST)
    cleaned_image.paste(mask_image, (0, 0), mask_image)
    # Then, if denoising was enabled, apply that next.
    if d_conf.denoising_enabled and path_gen.noise_mask.is_file():
        noise_mask = Image.open(path_gen.noise_mask)
        cleaned_image.paste(noise_mask, (0, 0), noise_mask)

    if i_conf.inpainting_fade_radius:
        # Fade the mask edges for a smoother transition.
        mask_faded = ops.fade_mask_edges(combined_mask, i_conf.inpainting_fade_radius)
    else:
        mask_faded = combined_mask.convert("L")

    # Cut away the rest according to the isolated combined mask.
    final_mask = Image.new("L", original_image.size, 0)
    final_mask.paste(mask_faded, (0, 0), isolated_combined_mask)
    inpainted_image.putalpha(final_mask)

    cleaned_image.alpha_composite(inpainted_image)
    cleaned_image.putalpha(255)

    # Save output.
    inpainted_image.save(path_gen.inpainting)
    cleaned_image.save(path_gen.clean_inpaint)

    # Package the analytics. We're only interested in the thicknesses.
    return st.InpaintingAnalytic(tuple(analytics_thicknesses), original_path)
