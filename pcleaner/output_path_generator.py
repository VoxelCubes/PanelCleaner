from uuid import uuid4
from pathlib import Path


class OutputPathGenerator:
    """
    Handle creating various output paths for all the different output options.
    """

    original_path: Path
    output_dir: Path

    # A suffix-free str that acts as a prefix for all cached file paths.
    _output_base_path: str

    def __init__(
        self,
        original_path: Path,
        output_dir: Path,
        uuid_source: Path | str | None = None,
        export_mode: bool = False,
    ) -> None:
        """
        Provide the original image path and cache dir to generate subsequent paths.
        Optionally, provide a path that contains the uuid to use the same one, otherwise
        a new uuid for clobber protection is generated.

        :param original_path: Image path of the input image.
        :param output_dir: The cache directory that intermediate images end up in.
        :param uuid_source: [Optional] a path with the uuid or the uuid as a string.
        :param export_mode: [Optional] when True, don't attempt to add a uuid.
        """
        self.original_path = original_path.resolve()
        self.output_dir = output_dir.resolve()
        if uuid_source is None:
            clobber_protection_prefix = uuid4()
        else:
            if isinstance(uuid_source, str):
                clobber_protection_prefix = uuid_source
            elif isinstance(uuid_source, Path):
                # Clobber protection prefixes have the form "{UUID}_file name"
                # ex. d91d86d1-b8d2-400b-98b2-2d0337973631_0023_myimage.png
                clobber_protection_prefix = uuid_source.stem.split("_")[0]
            else:
                raise TypeError("uuid_source expected to be Path, str, or None")

        if not export_mode:
            self._output_base_path = str(
                output_dir / f"{clobber_protection_prefix}_{original_path.stem}"
            )
        else:
            self._output_base_path = str(output_dir / original_path.stem)

    def _attach(self, suffix: str) -> Path:
        return Path(self._output_base_path + suffix)

    @property
    def base_png(self) -> Path:
        return self._attach(".png")

    @property
    def raw_mask(self) -> Path:
        return self._attach("_mask.png")

    @property
    def mask(self) -> Path:
        return self._attach("_mask.png")

    @property
    def raw_boxes(self) -> Path:
        return self._attach("_raw_boxes.png")

    @property
    def raw_json(self) -> Path:
        return self._attach("#raw.json")

    @property
    def clean_json(self) -> Path:
        return self._attach("#clean.json")

    @property
    def box_mask(self) -> Path:
        return self._attach("_box_mask.png")

    @property
    def with_masks(self) -> Path:
        return self._attach("_with_masks.png")

    @property
    def cut_mask(self) -> Path:
        return self._attach("_cut_mask.png")

    @property
    def mask_fitments(self) -> Path:
        return self._attach("_masks.png")

    @property
    def std_devs(self) -> Path:
        return self._attach("_std_devs.png")

    @property
    def combined_mask(self) -> Path:
        return self._attach("_combined_mask.png")

    @property
    def clean(self) -> Path:
        return self._attach("_clean.png")

    @property
    def text(self) -> Path:
        return self._attach("_text.png")

    @property
    def mask_data_json(self) -> Path:
        return self._attach("#mask_data.json")

    @property
    def noise_mask(self) -> Path:
        return self._attach("_noise_mask.png")

    @property
    def clean_denoised(self) -> Path:
        return self._attach("_clean_denoised.png")

    @property
    def inpainting_mask(self) -> Path:
        return self._attach("_inpainting_mask.png")

    @property
    def inpainting(self) -> Path:
        return self._attach("_inpainting.png")

    @property
    def clean_inpaint(self) -> Path:
        return self._attach("_clean_inpaint.png")
