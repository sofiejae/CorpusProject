import hashlib
import logging
import os
import pickle
import pathlib
from pathlib import Path

from tqdm import tqdm

from my_tools.Document import Document

logger = logging.getLogger(__name__)

# <project root>/Corpus/pickled, independent of the directory the program is started from
DEFAULT_CACHE_DIR = Path(__file__).resolve().parent.parent / "Corpus" / "pickled"


class _PortableUnpickler(pickle.Unpickler):
    """Unpickler that can read cache files made on any operating system.

    A pickled pathlib.PosixPath (made on Mac/Linux) cannot be loaded on Windows, and a WindowsPath
    cannot be loaded on Mac/Linux ("cannot instantiate 'PosixPath' on your system").
    We load all concrete paths as the OS-neutral pathlib.PurePath instead.
    """

    def find_class(self, module, name):
        # the module is "pathlib" on Python <= 3.12 and "pathlib._local" on Python >= 3.13
        if (module == "pathlib" or module.startswith("pathlib.")) and name in ("PosixPath", "WindowsPath"):
            return pathlib.PurePath
        return super().find_class(module, name)


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
            doc, error = self._read_pickle(pkl)
            if doc is None:
                self.failed.append((pkl.name, error))
            else:
                self.documents.append(doc)
        self._index = {doc.filename: doc for doc in self.documents}
        return self

    # ---------------------------------------------------------------- loading

    @staticmethod
    def _read_pickle(pickle_path):
        """Returns (document, None) on success and (None, error message) on failure."""
        try:
            with open(pickle_path, "rb") as f:
                return _PortableUnpickler(f).load(), None
        except Exception as e:  # corrupt or incompatible cache file
            logger.warning("Could not read cache file %s: %s", pickle_path, e)
            return None, f"{type(e).__name__}: {e}"

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
            doc = self._read_pickle(pickle_path)[0] if pickle_path.exists() else None

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

    # ---------------------------------------------------------------- access

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

    # ---------------------------------------------------------------- duplicates

    @staticmethod
    def _text_hash(doc):
        return