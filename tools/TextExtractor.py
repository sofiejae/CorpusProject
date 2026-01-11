import pdfminer.high_level as pdfhl

class TextExtractor():
    def __init__(self):
        pass

    def extract_pdf_text(self, file):
        #TODO: add a file check

        #TODO: read the filename

        # use pdf-miner to extract text
        text = pdfhl.extract_text(file)

        return text

if __name__ == "__main__":    
    te = TextExtractor()
    text = te.extract_pdf_text("Corpus/raw_data/22816484_Relinquishment_report_PL_679S.PDF")
    print(type(text))