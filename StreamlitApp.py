import os
from pathlib import Path

import pandas as pd
import streamlit as st

from my_tools.Corpus import Corpus, DEFAULT_CACHE_DIR
from my_tools.TextProcessor import TextProcessor

BASE_DIR = Path(__file__).resolve().parent
# folder with the raw PDFs; override with the CORPUS_PATH environment variable
DEFAULT_PDF_DIR = os.environ.get("CORPUS_PATH", str(BASE_DIR / "Corpus" / "raw_data"))

SOURCE_CACHE = "Cached documents"
SOURCE_PDFS = "PDF folder"
MAX_ROWS = 1000  # rows shown in a table; the CSV download always has everything

MODES = [
    "Concordance",
    "Word frequency",
    "Frequent words",
    "N-gram search",
    "Collocations",
    "Metadata viewer",
]


@st.cache_resource(show_spinner="Loading corpus ...")
def load_corpus(source, pdf_folder):
    """Cached across reruns, so the corpus is only built once per source."""
    if source == SOURCE_CACHE:
        return Corpus.from_cache()
    return Corpus(pdf_folder)


class StreamlitApp:
    def __init__(self, corpus_path=DEFAULT_PDF_DIR):
        st.set_page_config(page_title="Relinquishment Report Explorer", layout="wide")
        st.title("Relinquishment Report Explorer")

        self.processor = TextProcessor()
        self.corpus = self._load_corpus_from_sidebar(corpus_path)

        skip_dupes = st.sidebar.checkbox(
            "Skip duplicate documents", value=True,
            help="Some reports appear under several file IDs. Duplicates would count twice in all statistics.",
        )
        self.documents = self.corpus.unique_documents() if skip_dupes else list(self.corpus.documents)

        skipped = len(self.corpus.documents) - len(self.documents)
        st.sidebar.write(f"Loaded {len(self.documents)} documents" + (f" ({skipped} duplicates skipped)" if skipped else ""))
        if self.corpus.failed:
            first_name, first_error = self.corpus.failed[0]
            st.sidebar.warning(f"{len(self.corpus.failed)} file(s) could not be read. "
                               f"First problem: {first_name}: {first_error}")
        if not self.documents:
            st.warning("No documents found. Choose another source, or add PDFs to the folder.")
            st.stop()

        self.mode = st.sidebar.radio("Choose analysis mode", MODES)
        self.run()

    # ------------------------------------------------------------ setup / helpers

    def _load_corpus_from_sidebar(self, corpus_path):
        has_cache = DEFAULT_CACHE_DIR.is_dir() and any(DEFAULT_CACHE_DIR.glob("*.pkl"))
        source = st.sidebar.radio("Corpus source", [SOURCE_CACHE, SOURCE_PDFS], index=0 if has_cache else 1)

        pdf_folder = corpus_path
        if source == SOURCE_PDFS:
            pdf_folder = st.sidebar.text_input("PDF folder", value=corpus_path)
        try:
            return load_corpus(source, pdf_folder)
        except FileNotFoundError as e:
            st.error(str(e))
            st.stop()

    def _doc_choise(self):
        return st.selectbox("Document", ["All documents"] + [doc.filename for doc in self.documents])

    def _selected_docs(self, doc_choice):
        if doc_choice == "All documents":
            return self.documents
        return [doc for doc in self.documents if doc.filename == doc_choice]

    @staticmethod
    def _show_table(df, csv_name):
        if len(df) > MAX_ROWS:
            st.caption(f"Showing the first {MAX_ROWS} of {len(df)} rows. The CSV download has all of them.")
        st.dataframe(df.head(MAX_ROWS))
        st.download_button("Download CSV", df.to_csv(index=False).encode("utf-8"),
                           file_name=csv_name, mime="text/csv")

    def run(self):
        if self.mode == "Concordance":
            self.show_concordance()
        elif self.mode == "Word frequency":
            self.show_word_frequency()
        elif self.mode == "Frequent words":
            self.show_frequencies()
        elif self.mode == "N-gram search":
            self.show_n_grams()
        elif self.mode == "Collocations":
            self.show_collocations()
        elif self.mode == "Metadata viewer":
            self.show_metadata()

    # ------------------------------------------------------------ analysis modes

    def show_concordance(self):
        st.header("Concordance")
        search_word = st.text_input("Search word or phrase:").strip()
        window = st.slider("Context window", 2, 20, 5)
        docs = self._selected_docs(self._doc_choise())

        if not search_word:
            st.info("Enter a word to search.")
            return

        rows = []
        for doc in docs:  # per document, so contexts never run across document boundaries
            for left, token, right in TextProcessor.concordance(doc.tokens, search_word, window):
                rows.append((doc.filename, left, token, right))
        df = pd.DataFrame(rows, columns=["document", "left", "token", "right"])

        st.write(f"{len(df)} hits in {df['document'].nunique()} document(s)")
        if df.empty:
            return
        self._show_table(df, "concordance.csv")

    def show_word_frequency(self):
        st.header("Word frequency")
        search_word = st.text_input("Search word:").strip().lower()
        docs = self._selected_docs(self._doc_choise())

        if not search_word:
            st.info("Enter a word to search.")
            return

        per_doc = [(doc.filename, TextProcessor.token_freq(doc.tokens, search_word), doc.nr_tokens) for doc in docs]
        count = sum(c for _, c, _ in per_doc)
        total = sum(n for _, _, n in per_doc)
        n_docs = sum(1 for _, c, _ in per_doc if c)
        per_thousand = 1000 * count / total if total else 0

        st.write(f"Frequency of '{search_word}': {count} ({per_thousand:.2f} per 1,000 tokens), "
                 f"in {n_docs} of {len(docs)} document(s)")

        if len(docs) > 1 and count:
            df = pd.DataFrame(
                [(name, c, 1000 * c / n if n else 0) for name, c, n in per_doc if c],
                columns=["document", "count", "per 1,000 tokens"],
            ).sort_values("count", ascending=False)
            self._show_table(df, f"frequency_{search_word}.csv")

    def show_frequencies(self):
        st.header("Frequent words")
        docs = self._selected_docs(self._doc_choise())
        tokens = self.corpus.get_all_tokens(docs)

        remove_stop = st.checkbox("Exclude grammatical words (stopwords)")
        remove_punct = st.checkbox("Exclude punctuation tokens")
        tokens = TextProcessor.clean_tokens(tokens, remove_stop, remove_punct)

        fdist = self.processor.freq_dist(tokens)
        top_n = st.slider("Top N words", 10, 200, 50)

        items = fdist.most_common(top_n)
        df = pd.DataFrame(items, columns=["Word", "Frequency"])
        self._show_table(df, "frequent_words.csv")

    def show_n_grams(self):
        st.header("N-gram search")
        search_word = st.text_input("Search word (leave empty for all n-grams):").strip()
        n = st.slider("n (size of n-grams)", 2, 6, 3)
        position_label = st.radio("Position of the search word", ["anywhere", "first", "last"], horizontal=True)
        top_n = st.slider("Show top N n-grams", 10, 200, 50)
        docs = self._selected_docs(self._doc_choise())

        position = {"anywhere": "any", "first": "first", "last": "last"}[position_label]
        counts = {}
        for doc in docs:  # per document, so n-grams never span two documents
            for gram, c in TextProcessor.ngram_counts(doc.tokens, search_word or None, n, position).items():
                counts[gram] = counts.get(gram, 0) + c

        st.write(f"Found {sum(counts.values())} matches ({len(counts)} different n-grams)")
        if not counts:
            return
        ranked = sorted(counts.items(), key=lambda kv: (-kv[1], kv[0]))[:top_n]
        df = pd.DataFrame([(" ".join(gram), c) for gram, c in ranked], columns=["n-gram", "Frequency"])
        self._show_table(df, "ngrams.csv")

    def show_collocations(self):
        st.header("Collocations")
        search_word = st.text_input("Node word:").strip().lower()
        window = st.slider("Window (tokens on each side)", 1, 10, 4)
        min_freq = st.number_input("Minimum co-occurrence frequency", 1, 100, 3)
        measure_label = st.selectbox("Rank by", ["logDice", "PMI", "Frequency"])
        exclude_stop = st.checkbox("Exclude grammatical words (stopwords)", value=True)
        docs = self._selected_docs(self._doc_choise())

        if not search_word:
            st.info("Enter a word to search.")
            return

        measure = {"logDice": "logdice", "PMI": "pmi", "Frequency": "freq"}[measure_label]
        rows = TextProcessor.collocates([doc.tokens for doc in docs], search_word,
                                        window=window, min_freq=int(min_freq),
                                        measure=measure, exclude_stopwords=exclude_stop)
        if not rows:
            st.info(f"No collocates found for '{search_word}' with these settings.")
            return
        df = pd.DataFrame(rows).rename(columns={
            "collocate": "Collocate", "cooccurrence": "Co-occurrences",
            "collocate_freq": "Collocate frequency", "pmi": "PMI", "logdice": "logDice",
        }).round({"PMI": 2, "logDice": 2})
        self._show_table(df, f"collocates_{search_word}.csv")

    def show_metadata(self):
        st.header("Metadata viewer")

        rows = []
        for doc in self.documents:
            meta = doc.filename_metadata()
            rows.append({
                "document": doc.filename,
                "file id": meta["file_id"],
                "licence(s)": ", ".join(meta["licences"]),
                "tokens": doc.nr_tokens,
                "unique words": len(set(doc.tokens)),
                "characters": doc.char_number,
            })
        self._show_table(pd.DataFrame(rows), "metadata.csv")

        st.subheader("AI-extracted metadata (optional)")
        st.caption("Sends the first ~3000 characters of the chosen document to the OpenAI API. "
                   "Needs OPENAI_API_KEY in .streamlit/secrets.toml or as an environment variable.")
        choice = st.selectbox("Document to analyse", [d.filename for d in self.documents], key="meta_doc")
        if st.button("Extract metadata with AI"):
            doc = next(d for d in self.documents if d.filename == choice)
            try:
                from my_tools.GenAIClient import GenAIClient  # imported here so the app runs without openai/key
                with st.spinner("Asking the model ..."):
                    meta = doc.extract_metadata_with_ai(GenAIClient())
                st.session_state.setdefault("ai_meta", {})[choice] = meta
            except Exception as e:
                st.error(f"Could not extract metadata: {e}")

        ai_results = st.session_state.get("ai_meta", {})
        if ai_results:
            st.dataframe(pd.DataFrame([{"document": name, **meta} for name, meta in ai_results.items()]))


if __name__ == "__main__":
    StreamlitApp()