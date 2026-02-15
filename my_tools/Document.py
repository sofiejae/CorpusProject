import pdfminer.high_level as pdfhl
from pathlib import Path
from OCRProcessor import OCRProcessor
import nltk
import os
import re

class Document():
    def __init__(self, file_path, character_threshold=1000):
        # store data about filename and path
        self.file_path = Path(file_path)
        self.filename = os.path.basename(file_path)

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

    def _check_file_type(self):
        if self.file_path.suffix.lower() == ".pdf":
            return True
        
    def extract_pdf_text(self):
        #check wether pdf
        if not self._check_file_type():
            return

        # use pdf-miner to extract text
        text = pdfhl.extract_text(self.file_path)

        return text
    
    def _tokenize(self):
        lowered_text = self.text.lower()
        tokens = nltk.word_tokenize(lowered_text, preserve_line=True)

        return tokens
    
    def clean_text(self, text:str):
        """
        Cleans OCR-extracted text:
        - Removes multiple line breaks
        - Removes page numbers, headers, footers
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

        cleaned_text = text

        return cleaned_text
    
    def take_tokens_from_image_pages(self, threshold):
        text = OCRProcessor.pdf_text_image_to_string(self.file_path)

        return text

    
    #def extract_metadata_with_ai(self, genai: GenAIClient): """Use GenAI to extract metadata.""" ai_meta = genai.extract_metadata(self.first_page_text) self.metadata["ai_extracted"] = ai_meta

if __name__ == "__main__":    
    doc = Document("Corpus/raw_data/22816484_Relinquishment_report_PL_679S.PDF")
    print(type(doc))