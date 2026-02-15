import os
from Document import Document
from tqdm import tqdm
from pathlib import Path
import sys
import pickle

class Corpus():
    def __init__(self, folder_path):
        self.folderpath = folder_path
        self.documents = self._load_documents()

    def _load_documents(self):
        documents = []
        
        for filename in tqdm(os.listdir(self.folderpath), desc="Documents", position=0, leave=False):
            filepath = os.path.join(self.folderpath, filename)
            filename = Path(filepath).name
            pickle_path = Path("Corpus/pickled") / (filename + ".pkl")

            # Load cached document if exists
            if os.path.exists(pickle_path):
                with open(pickle_path, "rb") as f:
                    doc = pickle.load(f)
            else:
                doc = Document(filepath)

            # Save for next time
            with open(pickle_path, "wb") as f:
                pickle.dump(doc, f)

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