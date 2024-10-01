from pathlib import Path
import shutil

from PIL import Image
from loguru import logger

import pcleaner.image_ops as ops
import pcleaner.structures as st
import pcleaner.output_structures as ost


def denoise_page(d_data: st.DenoiserData) -> st.DenoiseAnalytic:
    """
    Load the MaskData from the json file and perform the denoising process.

    :param d_data: All the data needed for the denoising process.
    :return: Analytics.
    """
    # Load all the cached data.
    mask_data = st.MaskData.from_json(d_data.json_path.read_text(encoding="utf-8"))
    mask_image = Image.open(mask_data.mask_path)

    original_path = Path(mask_data.original_path)
    path_gen = ost.OutputPathGenerator(original_path, d_data.cache_dir, d_data.json_path)

    def save_mask(img, path: Path) -> None:
        img.save(path)

    cleaned_image = Image.open(mask_data.original_path)
    # Check if we're dealing with a 1-bit image.
    # Denoising these is pointless, as they have no noise.
    if cleaned_image.mode == "1":
        logger.info(f"Skipping pointless denoising for 1-bit image: {original_path}")
        # We can simply copy the cleaned output from the masker step.
        shutil.copyfile(path_gen.clean, path_gen.clean_denoised)
        # The noise mask is just a blank image with with the same size as the original.
        blank_noise_mask = Image.new("LA", cleaned_image.size, (0, 0))
        save_mask(blank_noise_mask, path_gen.noise_mask)
        return st.DenoiseAnalytic(tuple(), original_path)

    # Scale the mask to the original image size, if needed.
    cleaned_image = cleaned_image.convert("RGB")
    scale_up_factor = 1.0
    if cleaned_image.size != mask_image.size:
        scale_up_factor = cleaned_image.size[0] / mask_image.size[0]
        mask_image = mask_image.resize(cleaned_image.size, resample=Image.NEAREST)

    cleaned_image.paste(mask_image, (0, 0), mask_image)
    original_path: Path = mask_data.original_path

    # Alias.
    d_conf = d_data.denoiser_config

    # Filter for the min deviation to consider for denoising.
    boxes_to_denoise: list[st.Box] = [
        box
        for box, deviation, failed, _ in mask_data.boxes_with_stats
        if not failed and deviation > d_conf.noise_min_standard_deviation
    ]

    noise_masks_with_coords: list[tuple[Image.Image, tuple[int, int]]] = [
        ops.generate_noise_mask(cleaned_image, mask_image, box, d_conf, scale_up_factor)
        for box in boxes_to_denoise
    ]

    if noise_masks_with_coords:
        combined_noise_mask = ops.combine_noise_masks(cleaned_image.size, noise_masks_with_coords)
        cleaned_image.paste(combined_noise_mask, (0, 0), combined_noise_mask)
    else:
        # noinspection PyTypeChecker
        combined_noise_mask = Image.new("LA", cleaned_image.size, (0, 0))

    save_mask(combined_noise_mask, path_gen.noise_mask)
    save_mask(cleaned_image, path_gen.clean_denoised)

    # Package the analytics. We're only interested in the std deviations.
    return st.DenoiseAnalytic(
        tuple(deviation for _, deviation, _, _ in mask_data.boxes_with_stats), original_path
    )
