import hashlib
import logging
import os
import pickle
from pathlib import Path

from tqdm import tqdm

from my_tools.Document import Document

logger = logging.getLogger(__name__)

# <project root>/Corpus/pickled, independent of the directory the program is started from
DEFAULT_CACHE_DIR = Path(__file__).resolve().parent.parent / "Corpus" / "pickled"


class Corpus:
    """A collection of Documents.

    Corpus("path/to/pdfs")   reads every PDF in the folder (text extraction/OCR is slow, so each
                             processed document is cached as a .pkl file in `cache_dir`).
    Corpus.from_cache()      loads only the cached documents; no PDFs needed.

    Note: the cache uses pickle, so only load .pkl files you trust.
    """

    def __init__(self, folder_path, cache_dir=DEFAULT_CACHE_DIR):
        self.folderpath = folder_path
        self.cache_dir = Path(cache_dir)
        self.failed = []  # (filename, error message) for documents that could not be processed
        self.documents = self._load_documents()
        self._index = {doc.filename: doc for doc in self.documents}

    @classmethod
    def from_cache(cls, cache_dir=DEFAULT_CACHE_DIR):
        """Build a corpus from the cached documents only."""
        self = cls.__new__(cls)
        self.folderpath = None
        self.cache_dir = Path(cache_dir)
        self.failed = []
        self.documents = []
        if not self.cache_dir.is_dir():
            raise FileNotFoundError(f"Cache folder not found: {self.cache_dir}")
        for pkl in tqdm(sorted(self.cache_dir.glob("*.pkl")), desc="Cached documents", leave=False):
            doc = self._read_pickle(pkl)
            if doc is None:
                self.failed.append((pkl.name, "could not read cache file"))
            else:
                self.documents.append(doc)
        self._index = {doc.filename: doc for doc in self.documents}
        return self

    @staticmethod
    def _read_pickle(pickle_path):
        try:
            with open(pickle_path, "rb") as f:
                return pickle.load(f)
        except Exception as e:  # corrupt or incompatible cache file
            logger.warning("Could not read cache file %s: %s", pickle_path, e)
            return None

    def _write_pickle(self, doc, pickle_path):
        try:
            self.cache_dir.mkdir(parents=True, exist_ok=True)
            with open(pickle_path, "wb") as f:
                pickle.dump(doc, f)
        except OSError as e:  # a read-only folder should not stop the analysis
            logger.warning("Could not write cache file %s: %s", pickle_path, e)

    def _load_documents(self):
        if not os.path.isdir(self.folderpath):
            raise FileNotFoundError(f"Corpus folder not found: {self.folderpath}")

        documents = []
        filenames = sorted(f for f in os.listdir(self.folderpath) if f.lower().endswith(".pdf"))

        for filename in tqdm(filenames, desc="Documents", position=0, leave=False):
            filepath = os.path.join(self.folderpath, filename)
            pickle_path = self.cache_dir / (filename + ".pkl")

            # use the cached document if there is one
            doc = self._read_pickle(pickle_path) if pickle_path.exists() else None

            if doc is None:
                try:
                    doc = Document(filepath)
                except Exception as e:  # one broken PDF should not stop the whole corpus
                    logger.warning("Skipping %s: %s", filename, e)
                    self.failed.append((filename, str(e)))
                    continue
                self._write_pickle(doc, pickle_path)  # only save newly processed documents

            documents.append(doc)

        return documents

    def __len__(self):
        return len(self.documents)

    def __iter__(self):
        return iter(self.documents)

    def get_document(self, filename):
        return self._index.get(filename)

    def get_all_tokens(self, documents=None):
        tokens = []
        for doc in (self.documents if documents is None else documents):
            tokens.extend(doc.tokens)
        return tokens

    @staticmethod
    def _text_hash(doc):
        return hashlib.sha1(doc.text.encode("utf-8")).hexdigest()

    def duplicate_groups(self):
        """Groups of documents with identical text (the same report filed under several IDs)."""
        groups = {}
        for doc in self.documents:
            groups.setdefault(self._text_hash(doc), []).append(doc.filename)
        return [names for names in groups.values() if len(names) > 1]

    def unique_documents(self):
        """The documents, keeping only the first of each group of identical texts.
        Duplicates would otherwise count twice in frequencies and collocations."""
        seen = set()
        unique = []
        for doc in self.documents:
            h = self._text_hash(doc)
            if h not in seen:
                seen.add(h)
                unique.append(doc)
        return unique


if __name__ == "__main__":
    import sys

    folder = sys.argv[1] if len(sys.argv) > 1 else "Corpus/raw_data/"
    corp = Corpus(folder)
    print(f"Loaded {len(corp)} documents, {len(corp.get_all_tokens())} tokens")