from tests.helpers import mock_file_path
import pcleaner.image_ops as ops
import time


def test_split_image():
    image_path = mock_file_path("long_strip.jpg")

    preferred_height = 2000
    tolerance = 1000

    start = time.time()
    splits = ops.calculate_best_splits(
        image_path,
        preferred_height,
        tolerance,
        split_strips=True,
        max_aspect_ratio=0.3,
    )
    assert True

    if True:
        return

    print(f"Time taken: {(time.time() - start) * 1000:.2f} ms")
    print("Splits:")
    print(splits)

    # Draw the splits.
    from PIL import Image, ImageDraw
    from math import ceil

    image = Image.open(image_path)
    draw = ImageDraw.Draw(image)
    height = image.height
    num_strips = ceil(height / preferred_height) - 1
    preferred_height = height // (num_strips + 1)
    for index, split in enumerate(splits, 1):
        initial_split = preferred_height * index
        draw.line(
            (0, initial_split - tolerance, image.width, initial_split - tolerance),
            fill="blue",
            width=2,
        )
        draw.line((0, split, image.width, split), fill="red", width=5)
        draw.line(
            (0, initial_split + tolerance, image.width, initial_split + tolerance),
            fill="blue",
            width=2,
        )
        draw.line(
            (0, initial_split, image.width, initial_split),
            fill="green",
            width=2,
        )

    image.show()
