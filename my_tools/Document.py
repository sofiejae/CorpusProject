import pdfminer.high_level as pdfhl
from pathlib import Path
import nltk
import os

class Document():
    def __init__(self, file_path):
        self.file_path = Path(file_path)
        self.filename = os.path.basename(file_path)
        self.text = self._extract_pdf_text()
        self.tokens = self._tokenize()

    def _check_file_type(self):
        if self.file_path.suffix.lower() == ".pdf":
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
    
    #def extract_metadata_with_ai(self, genai: GenAIClient): """Use GenAI to extract metadata.""" ai_meta = genai.extract_metadata(self.first_page_text) self.metadata["ai_extracted"] = ai_meta

if __name__ == "__main__":    
    doc = Document("Corpus/raw_data/22816484_Relinquishment_report_PL_679S.PDF")
    print(type(doc))