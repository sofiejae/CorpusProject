import os
from my_tools.Document import Document

class Corpus():
    def __init__(self, folder_path):
        self.folderpath = folder_path
        self.documents = self._load_documents()

    def _load_documents(self):
        documents = []
        
        for filename in os.listdir(self.folderpath):
            filepath = os.path.join(self.folderpath, filename)
            doc = Document(filepath)
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
    corp = Corpus("Corpus/raw_data/")