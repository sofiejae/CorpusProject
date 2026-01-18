import os
from Document import Document

class Corpus():
    def __init__(self, folder_path):
        self.folderpath = folder_path
        self.documents = self._load_documents()

    def _load_documents(self):
        documents = []
        
        for filename in os.listdir(self.folderpath):
            filepath = os.path.join(self.folderpath, filename)
            doc = Document(filepath)
            
            # check if there is text in image pages
            doc.take_tokens_from_image_pages()
            
            # add reaction if doc was not pdf
            documents.append(doc)

        return documents

    def get_document(self, filename): 
        for doc in self.documents: 
            if doc.filename == filename: 
                return doc 
            return None
    
    def get_all_tokens(self):
        tokens = []

        for doc in self.documents:
            tokens.extend(doc.tokens)

        return tokens

if __name__ == "__main__":
    corp = Corpus('/Users/sofiebenjaminsen/Library/CloudStorage/GoogleDrive-sofiejb@gmail.com/Min disk/Colab Notebooks/NPD relinquishment reports - 30-12-2025')
    #corp = Corpus("Corpus/raw_data/")