import pdfminer.high_level as pdfhl
from pathlib import Path
from OCRProcessor import OCRProcessor
import nltk
import os

class Document():
    def __init__(self, file_path):
        self.file_path = Path(file_path)
        self.filename = os.path.basename(file_path)
        self.text = self._extract_pdf_text()
        self.char_number = len(self.text.strip())
        self.tokens = self._tokenize()

    def _check_file_type(self):
        if self.file_path.suffix.lower() == ".pdf":
            return True
    
    def _tokens_above_threshold(self, threshold):
        """Check whether there are very few words, meaning text as image in the pdf"""
        if len(self.tokens) < threshold:
            return False
        return True
        
    def _extract_pdf_text(self):
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
    
    def take_tokens_from_image_pages(self, threshold=1000):
        if not self._tokens_above_threshold(threshold):
            text = OCRProcessor.pdf_text_image_to_string(self.file_path)

            self.text = text

    
    #def extract_metadata_with_ai(self, genai: GenAIClient): """Use GenAI to extract metadata.""" ai_meta = genai.extract_metadata(self.first_page_text) self.metadata["ai_extracted"] = ai_meta

if __name__ == "__main__":    
    doc = Document("Corpus/raw_data/22816484_Relinquishment_report_PL_679S.PDF")
    print(type(doc))