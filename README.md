# CorpusProject
Basic tools for corpus linguistics on the NPD relinquishment reports (PDF), with a Streamlit front end.

## Features
- **Concordance (KWIC)** for words or phrases, per document or for the whole corpus
- **Word frequency** (raw and per 1,000 tokens, with a per-document breakdown)
- **Frequent words**, optionally without stopwords/punctuation
- **N-gram search** (search word anywhere / first / last in the n-gram)
- **Collocations** ranked by logDice, PMI or frequency
- **Metadata viewer**: tokens, vocabulary size, licence numbers from the file names, and optional AI extraction (OpenAI)
- CSV download of every result table

## Setup
Create a local venv and install the packages: `pip install -r requirements.txt`
(Anaconda: `conda install --file requirements.txt`).

Only needed when you process **new PDFs** that turn out to be scans (OCR):
install [Tesseract](https://github.com/tesseract-ocr/tesseract) (macOS: `brew install tesseract`).
The program finds it on your PATH, or via the `TESSERACT_CMD` environment variable.

The AI metadata feature needs an OpenAI key, either in `.streamlit/secrets.toml`
(`OPENAI_API_KEY = "sk-..."`) or as the environment variable `OPENAI_API_KEY`. Everything else works without it.

## Run
```
streamlit run StreamlitApp.py
```
In the sidebar, choose the corpus source:
- **Cached documents** (default): the already processed reports in `Corpus/pickled/`. Fast, no PDFs needed.
- **PDF folder**: a folder of PDFs (default `Corpus/raw_data/`, or set the `CORPUS_PATH` environment variable).
  New PDFs are processed once and then cached in `Corpus/pickled/`.

Some reports exist under several file IDs. "Skip duplicate documents" (on by default) counts each text only once.

## Use from Python
```python
from my_tools.Corpus import Corpus
from my_tools.TextProcessor import TextProcessor

corpus = Corpus.from_cache()            # or Corpus("path/to/pdfs")
docs = corpus.unique_documents()
tokens = corpus.get_all_tokens(docs)
TextProcessor.concordance(tokens, "licence", width=5)
TextProcessor.collocates([d.tokens for d in docs], "well", window=4)
```

## Tests
```
python -m unittest discover -v
```

## Note on the cache
The `.pkl` files are Python pickles: only load cache files you made yourself or trust.