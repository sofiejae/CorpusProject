import io
import os
import shutil


def _configure_tesseract(pytesseract):
    """Find the tesseract binary on any OS.

    Order: TESSERACT_CMD environment variable -> PATH -> common Homebrew locations.
    If nothing is found we leave pytesseract's default and let it raise its own error.
    """
    cmd = os.environ.get("TESSERACT_CMD") or shutil.which("tesseract")
    if not cmd:
        for candidate in ("/opt/homebrew/bin/tesseract", "/usr/local/bin/tesseract"):
            if os.path.exists(candidate):
                cmd = candidate
                break
    if cmd:
        pytesseract.pytesseract.tesseract_cmd = cmd


class OCRProcessor:

    @staticmethod
    def pdf_text_image_to_string(pdf_file_path, dpi=300, lang="eng"):
        """OCR every page of a PDF (for scanned PDFs without a text layer) and return the text."""
        # Imported here so that loading cached documents does not require PyMuPDF/Tesseract.
        import pymupdf as mpdf
        import pytesseract
        from PIL import Image
        from tqdm import tqdm

        _configure_tesseract(pytesseract)

        # silence MuPDF warnings such as: Cannot set gray non-stroke color because /'P2' is an invalid float value
        mpdf.TOOLS.mupdf_display_errors(False)

        texts = []
        with mpdf.open(pdf_file_path) as doc:
            for page in tqdm(doc, desc="Pages", position=1, leave=False, total=len(doc)):
                pix = page.get_pixmap(colorspace=mpdf.csRGB, dpi=dpi)  # Page -> Pixmap
                img = Image.open(io.BytesIO(pix.tobytes("png")))        # Pixmap -> PIL image
                texts.append(pytesseract.image_to_string(img, lang=lang).strip())  # OCR

        return " ".join(texts)