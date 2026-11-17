import os
import re
from pathlib import Path
from typing import TYPE_CHECKING

import nltk
import pdfminer.high_level as pdfhl

from my_tools.OCRProcessor import OCRProcessor

if TYPE_CHECKING:  # only needed for the type hint below; avoids a hard dependency on openai/streamlit
    from my_tools.GenAIClient import GenAIClient


CID_PATTERN = re.compile(r"\(cid:\d+\)")


class Document:
    def __init__(self, file_path, character_threshold=1000):
        # store data about filename and path
        self.file_path = Path(file_path)
        self.filename = os.path.basename(file_path)
        self.metadata = {}

        # extract the text from the document (first strings, second OCR, then clean)
        string_text = self.extract_pdf_text()

        if len(string_text) < character_threshold:
            ocr_text = self.take_tokens_from_image_pages(threshold=character_threshold)
            cleaned_text = self.clean_text(string_text + ocr_text)
        else:
            cleaned_text = self.clean_text(string_text)

        self.text = cleaned_text
        # get text length and tokens
        self.char_number = len(self.text.strip())
        self.tokens = self._tokenize()
        self.nr_tokens = len(self.tokens)

    def __setstate__(self, state):
        """Called when unpickling. Lets documents cached by an older version of this class
        (which had no `metadata` attribute) load without errors."""
        self.__dict__.update(state)
        self.__dict__.setdefault("metadata", {})
        self._strip_cid_garbage()

    def _strip_cid_garbage(self):
        """Documents cached before the "(cid:123)" fix contain the tokens 'cid', '123'. Remove them."""
        if "cid" not in self.tokens:
            return
        cleaned, i = [], 0
        while i < len(self.tokens):
            if self.tokens[i] == "cid" and i + 1 < len(self.tokens) and self.tokens[i + 1].isdigit():
                i += 2
            else:
                cleaned.append(self.tokens[i])
                i += 1
        self.tokens = cleaned
        self.nr_tokens = len(cleaned)
        self.text = re.sub(r"\bcid \d+\b", " ", self.text)
        self.text = re.sub(r"\s+", " ", self.text)
        self.char_number = len(self.text.strip())

    def __repr__(self):
        return f"Document({self.filename!r}, tokens={self.nr_tokens})"

    @property
    def first_page_text(self):
        """Approximation of the title page: the start of the cleaned text (used for AI metadata extraction)."""
        return self.text[:3000]

    def _check_file_type(self):
        return self.file_path.suffix.lower() == ".pdf"

    def extract_pdf_text(self):
        # use pdf-miner to extract text
        text = pdfhl.extract_text(self.file_path)
        # Fonts without a usable encoding come out as "(cid:123)" placeholders. Strip them here, so that a
        # PDF where this is most of the text counts as "too little text" and falls back to OCR.
        return CID_PATTERN.sub(" ", text)

    def _tokenize(self):
        lowered_text = self.text.lower()
        # preserve_line=True skips sentence splitting, so no nltk 'punkt' download is needed
        return nltk.word_tokenize(lowered_text, preserve_line=True)

    def clean_text(self, text: str):
        """
        Cleans extracted text:
        - Removes multiple line breaks
        - Removes page numbers like "2 of 12", and figure references
        - Removes all punctuation/symbols (so tokens are plain words and numbers)
        """

        # 1. Normalize line breaks & spaces
        text = text.replace("\n", " ").replace("\r", " ")
        text = re.sub(r"\s+", " ", text)  # collapse multiple spaces

        # 2. Remove repeated headings / page markers like numbers like "2 of 12"
        text = re.sub(r"\d+\s+of\s+\d+", "", text)

        # 3. Remove figure references like "Figure 1.1" or "Fig 1.1"
        text = re.sub(r"(Figure|Fig)\s+\d+(\.\d+)?", "", text)

        # 4. Remove weird symbols and OCR artifacts
        text = re.sub(r"[^\w\s]", " ", text)  # keep only letters/numbers/underscore
        text = re.sub(r"_+", " ", text)       # collapse underscores

        return text

    def take_tokens_from_image_pages(self, threshold):
        return OCRProcessor.pdf_text_image_to_string(self.file_path)

    def filename_metadata(self):
        """Metadata that can be read straight from the NPD file name, e.g.
        '20108101_Relinquishment_report_PL_506S_506BS.pdf' -> file_id '20108101', licences ['506S', '506BS']."""
        stem = Path(self.filename).stem
        file_id = stem.split("_")[0]
        match = re.search(r"PL_(.+)$", stem, flags=re.IGNORECASE)
        licences = []
        if match:
            licences = [
                part.upper()
                for part in match.group(1).split("_")
                if re.fullmatch(r"\d{2,3}[A-Za-z]{0,2}", part)
            ]
        return {"file_id": file_id, "licences": licences}

    def extract_metadata_with_ai(self, genai: "GenAIClient"):
        """Use GenAI to extract metadata (title, block, operator, date_issued)."""
        ai_meta = genai.extract_metadata(self.first_page_text)
        self.metadata["ai_extracted"] = ai_meta
        return ai_meta


if __name__ == "__main__":
    doc = Document("Corpus/raw_data/22816484_Relinquishment_report_PL_679S.PDF")
    print(doc, doc.filename_metadata())