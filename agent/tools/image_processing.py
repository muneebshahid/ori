"""Image processing pipeline for tool-returned images."""

from dataclasses import dataclass
from io import BytesIO

from PIL import Image, ImageOps

from ai.types.tools import ImageMimeType

EXIF_ORIENTATION_TAG = 274


@dataclass(frozen=True)
class ProcessedImage:
    """Image bytes and MIME metadata after local processing."""

    data: bytes
    mime_type: ImageMimeType


def process_image(data: bytes, mime_type: ImageMimeType) -> ProcessedImage:
    """Run the image processing pipeline before model submission."""

    oriented_data = _apply_exif_orientation(data, mime_type)
    return ProcessedImage(data=oriented_data, mime_type=mime_type)


def _apply_exif_orientation(data: bytes, mime_type: ImageMimeType) -> bytes:
    """Return image bytes with EXIF orientation applied when needed."""

    if mime_type != "image/jpeg":
        return data

    with Image.open(BytesIO(data)) as image:
        if not _has_exif_orientation(image):
            return data

        oriented_image = ImageOps.exif_transpose(image)
        output = BytesIO()
        _prepare_for_encoding(oriented_image, mime_type).save(
            output,
            format=_image_format(mime_type),
        )
        return output.getvalue()


def _has_exif_orientation(image: Image.Image) -> bool:
    """Return whether an image has a meaningful EXIF orientation tag."""

    orientation = image.getexif().get(EXIF_ORIENTATION_TAG, 1)
    return isinstance(orientation, int) and orientation != 1


def _prepare_for_encoding(
    image: Image.Image,
    mime_type: ImageMimeType,
) -> Image.Image:
    """Return an image mode compatible with the target encoder."""

    if mime_type == "image/jpeg" and image.mode not in ("RGB", "L"):
        return image.convert("RGB")
    return image


def _image_format(mime_type: ImageMimeType) -> str:
    """Return the Pillow save format for a MIME type."""

    match mime_type:
        case "image/jpeg":
            return "JPEG"
        case "image/png":
            return "PNG"
        case "image/gif":
            return "GIF"
        case "image/webp":
            return "WEBP"
