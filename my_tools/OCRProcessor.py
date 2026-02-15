import pytesseract
import pymupdf as mpdf
from PIL import Image
import io
import sys
import os
import warnings
from tqdm import tqdm


# give path to tesseract brew installation
pytesseract.pytesseract.tesseract_cmd = "/opt/homebrew/bin/tesseract"

# ignore warnings such as: Cannot set gray non-stroke color because /'P2' is an invalid float value
#warnings.filterwarnings("ignore", module="mpdf")


class OCRProcessor():
    
    @staticmethod
    def pdf_text_image_to_string(pdf_file_path):
        """takes a pdf with pages where """
        mpdf.TOOLS.mupdf_display_errors(False)
        doc = mpdf.open(pdf_file_path) 
        text = ""

        for page in tqdm(doc, desc="Pages", position=1, leave=False):
            pix = page.get_pixmap(colorspace=mpdf.csRGB, dpi=300) # Page → Pixmap 
            img_bytes = pix.tobytes("png") # Pixmap → PNG bytes 
            img = Image.open(io.BytesIO(img_bytes)) # Bytes → PIL Image 

            output = pytesseract.image_to_string(img).strip() # OCR

            text = text + " " + output

        return text