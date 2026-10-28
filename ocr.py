"""OCR subprocess uses file data only; never executes text recognized from screenshot."""
import io
import shutil
import subprocess
from PIL import Image, ImageOps


def extract_screenshot(data: bytes) -> str:
    if not shutil.which('tesseract'):
        raise RuntimeError('Tesseract OCR binary not installed. See README setup instructions.')
    if len(data) > 8_000_000:
        raise ValueError('Screenshot exceeds the 8 MB limit.')
    with Image.open(io.BytesIO(data)) as img:
        if img.width * img.height > 15_000_000:
            raise ValueError('Screenshot pixel count exceeds the safe limit.')
        img = ImageOps.autocontrast(img.convert('L'))
        buf = io.BytesIO()
        img.save(buf, format='PNG')
    result = subprocess.run(['tesseract', 'stdin', 'stdout', '--psm', '6'], input=buf.getvalue(), capture_output=True, timeout=25)
    if result.returncode:
        raise RuntimeError('OCR did not succeed. Try a higher-resolution screenshot.')
    return result.stdout.decode('utf-8', errors='replace')[:100_000]
