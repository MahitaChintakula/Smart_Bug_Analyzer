"""Optional OCR support for screenshots uploaded with a bug report."""

from io import BytesIO
import shutil
import subprocess
from tempfile import NamedTemporaryFile


class OCRServiceError(RuntimeError):
    """Raised when an uploaded image cannot be processed with OCR."""


def extract_text_from_image(image_bytes: bytes) -> str:
    """Extract readable text from an image using the local Tesseract engine."""
    try:
        from PIL import Image
    except ImportError as error:  # pragma: no cover - depends on the host runtime
        raise OCRServiceError(
            "Screenshot OCR is unavailable. Install Pillow."
        ) from error

    try:
        with Image.open(BytesIO(image_bytes)) as image:
            image.verify()
    except Exception as error:
        raise OCRServiceError("The uploaded file is not a valid image.") from error

    executable = shutil.which("tesseract")
    if not executable:
        raise OCRServiceError(
            "Screenshot OCR is unavailable because Tesseract is not installed. "
            "Install it with `brew install tesseract` or your system package manager."
        )

    try:
        with NamedTemporaryFile(suffix=".image") as image_file:
            image_file.write(image_bytes)
            image_file.flush()
            result = subprocess.run(
                [executable, image_file.name, "stdout", "--psm", "6"],
                capture_output=True,
                check=False,
                text=True,
                timeout=30,
            )
    except subprocess.TimeoutExpired as error:
        raise OCRServiceError(
            "Screenshot OCR timed out. Please use a smaller image."
        ) from error
    except Exception as error:
        raise OCRServiceError("The screenshot could not be read with OCR.") from error

    if result.returncode != 0:
        raise OCRServiceError("The screenshot could not be read with OCR.")

    return result.stdout.strip()
