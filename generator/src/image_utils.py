"""
Image optimization utilities for asset generation.

This module provides functions to optimize images for web delivery,
supporting both PNG optimization and WebP conversion with configurable
quality settings.
"""

import logging
from PIL import Image
from typing import Literal, Optional
from pathlib import Path

logger = logging.getLogger(__name__)

ImageFormat = Literal["png", "webp"]


def optimize_image(
    image: Image.Image,
    output_path: str,
    format: ImageFormat = "webp",
    quality: int = 85,
    lossless: bool = False,
) -> None:
   """
Optimize and save an image with specified format and quality settings.

Args:
    image: PIL Image object to optimize
    output_path: Path where the optimized image will be saved
    format: Output format - 'png' or 'webp'
    quality: Quality level for lossy compression (1–100)
    lossless: Whether to use lossless compression

Returns:
    None
"""

    if not 1 <= quality <= 100:
        raise ValueError("Quality must be between 1 and 100")

    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    logger.debug(
    f"Optimizing image -> format={format}, quality={quality}, lossless={lossless}"
)

    if format == "webp":
        _save_as_webp(image, output_path, quality, lossless)
    elif format == "png":
        _save_as_png(image, output_path)
    else:
        raise ValueError(f"Unsupported format: {format}. Use 'png' or 'webp'.")

    logger.debug(f"Saved optimized {format.upper()} image to {output_path}")


def _save_as_webp(
    image: Image.Image,
    output_path: Path,
    quality: int,
    lossless: bool
) -> None:
    """Save image as WebP with specified quality settings."""

    logger.debug(f"Saving image as WEBP: {output_path}")

    save_kwargs = {
        "format": "WebP",
        "lossless": lossless,
    }

    if not lossless:
        save_kwargs["quality"] = quality
        save_kwargs["method"] = 6

    image.save(output_path, **save_kwargs)


def _save_as_png(image: Image.Image, output_path: Path) -> None:
    """Save image as optimized PNG."""

    logger.debug(f"Saving image as PNG: {output_path}")

    image.save(
        output_path,
        format="PNG",
        optimize=True,
        compress_level=9
    )


def get_file_extension(format: ImageFormat) -> str:
    """
    Get the file extension for a given image format.
    """
    return f".{format}"


def convert_existing_image(
    input_path: str,
    output_path: Optional[str] = None,
    format: ImageFormat = "webp",
    quality: int = 85,
    lossless: bool = False,
) -> str:
    """
    Convert an existing image file to optimized format.
    """

    input_path = Path(input_path)

    if not input_path.exists():
        logger.error(f"Input image file not found: {input_path}")
        raise FileNotFoundError(f"Input image file not found: {input_path}")

    if output_path is None:
        output_path = input_path.with_suffix(get_file_extension(format))
    else:
        output_path = Path(output_path)

    logger.debug(f"Converting image {input_path} -> {output_path}")

    with Image.open(input_path) as img:

        # Convert RGBA to RGB if saving as format that doesn't support transparency
        if img.mode == "RGBA" and format not in ["png", "webp"]:
            logger.debug("Converting RGBA image to RGB")
            background = Image.new("RGB", img.size, (255, 255, 255))
            background.paste(img, mask=img.split()[3])
            img = background

        optimize_image(img, str(output_path), format, quality, lossless)

    logger.debug(f"Image conversion complete: {output_path}")

    return str(output_path)
