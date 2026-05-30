"""Tests for image processing before model submission."""

from io import BytesIO

from PIL import Image

from agent.tools.image_processing import process_image


def test_process_image_applies_jpeg_exif_orientation() -> None:
    """Rotate JPEG bytes according to their EXIF orientation tag."""

    original = _jpeg_with_orientation(width=2, height=3, orientation=6)

    processed = process_image(original, "image/jpeg")

    with Image.open(BytesIO(processed.data)) as image:
        assert processed.mime_type == "image/jpeg"
        assert image.size == (3, 2)
        assert image.getexif().get(274) is None


def test_process_image_preserves_jpeg_without_exif_orientation() -> None:
    """Leave JPEG bytes unchanged when there is no EXIF orientation work."""

    original = _jpeg(width=2, height=3)

    processed = process_image(original, "image/jpeg")

    assert processed.data == original
    assert processed.mime_type == "image/jpeg"


def test_process_image_preserves_non_jpeg_bytes() -> None:
    """Leave non-JPEG image bytes unchanged for the first pipeline step."""

    original = b"not-real-png-bytes"

    processed = process_image(original, "image/png")

    assert processed.data == original
    assert processed.mime_type == "image/png"


def _jpeg(width: int, height: int) -> bytes:
    """Return JPEG bytes for a solid-color image."""

    image = Image.new("RGB", (width, height), "red")
    output = BytesIO()
    image.save(output, format="JPEG")
    return output.getvalue()


def _jpeg_with_orientation(width: int, height: int, orientation: int) -> bytes:
    """Return JPEG bytes containing an EXIF orientation tag."""

    image = Image.new("RGB", (width, height), "red")
    exif = Image.Exif()
    exif[274] = orientation
    output = BytesIO()
    image.save(output, format="JPEG", exif=exif)
    return output.getvalue()
