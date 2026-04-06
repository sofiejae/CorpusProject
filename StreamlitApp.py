import os
import streamlit as st
import pandas as pd
from my_tools.Corpus import Corpus
from my_tools.Document import Document
from my_tools.TextProcessor import TextProcessor

class StreamlitApp():
    def __init__(self, corpus_path = "Corpus/raw_data/"):
        # retrieve the API-key for the genAImodel
        #api_key = st.secrets["OPENAI_KEY"]
        
        # create ciorus and processor objects
        self.corpus = Corpus(corpus_path) 
        self.processor = TextProcessor()

        # set up stramlit app
        st.title = "Relinquishment Report Explorer"
        st.sidebar.write(f"Loaded {len(self.corpus.documents)} documents")

        self.mode = st.sidebar.radio( "Choose analysis mode", ["Concordance", "Word frequency", "Frequent words", "N-gram search", "Metadata viewer"] ) 
        
        self.run()

    def _doc_choise(self):
        doc_choice = st.selectbox( "Document", ["All documents"] + [doc.filename for doc in self.corpus.documents])
        return doc_choice

    def _get_doc_choice(self, doc_choice):
        if doc_choice == "All documents": 
            tokens = self.corpus.get_all_tokens() 
        else: 
            tokens = self.corpus.get_document(doc_choice).tokens
        
        return tokens


    def run(self):
        if self.mode == "Concordance":
            self.show_concordance()
        elif self.mode == "Frequent words":
            self.show_frequencies()
        elif self.mode == "Word frequency":
            self.show_word_frequency()

    def show_metadata(self):

        pass

    def show_concordance(self):
        st.header("Concordance") 
        search_word = st.text_input("Search word:") 
        window = st.slider("Context window", 2, 20, 5)

        if not search_word: 
            st.info("Enter a word to search.")
            return

        doc_choice = self._doc_choise()
        tokens = self._get_doc_choice(doc_choice)

        results = TextProcessor.concordance(tokens, search_word, window)
        df = pd.DataFrame(results, columns=["left", "token", "right"])

        st.dataframe(df)

    def show_word_frequency(self):
        st.header("Word frequency")

        search_word = st.text_input("Search word:").lower()
        if not search_word: 
            st.info("Enter a word to search.") 
            return

        doc_choice = self._doc_choise()
        tokens = self._get_doc_choice(doc_choice)

        count = TextProcessor.token_freq(tokens=tokens, target=search_word)
        st.write(f"Frekvens for '{search_word}': {count}")
        


    def show_frequencies(self):
        st.header("Frequent words")

        doc_choice = st.selectbox( 
            "Document", ["All documents"] + [doc.filename for doc in self.corpus.documents] 
        )

        if doc_choice == "All documents": 
            tokens = self.corpus.get_all_tokens()
        else: 
            tokens = self.corpus.get_document(doc_choice).tokens

        remove_stop = st.checkbox("Exclude grammatical words (stopwords)") 
        remove_punct = st.checkbox("Exclude punctuation tokens")

        tokens = TextProcessor.clean_tokens(tokens, remove_stop, remove_punct)

        fdist = self.processor.freq_dist(tokens) 
        top_n = st.slider("Top N words", 10, 200, 50)

        items = fdist.most_common(top_n) 
        st.table({"Word": [w for w, _ in items], "Frequency": [f for _, f in items]})

    def show_n_grams(self):
        st.header("N-gram search") 
        search_word = st.text_input("Search word:") 
        n = st.slider("n (size of n-grams)", 2, 6, 3) 
        doc_choice = st.selectbox( "Document", ["All documents"] + [doc.filename for doc in self.corpus.documents] ) 
        if not search_word: 
            st.info("Enter a word to search.") 
            return 
        if doc_choice == "All documents": 
            tokens = self.corpus.all_tokens() 
        else: 
            tokens = self.corpus.get_document(doc_choice).tokens 
            hits = self.analyzer.ngram_search(tokens, search_word, n) 
            st.write(f"Found {len(hits)} matches") 
            for gram in hits[:100]: 
                st.markdown(" ".join(gram))

if __name__ == "__main__":
    StreamlitApp('/Users/sofiebenjaminsen/Library/CloudStorage/GoogleDrive-sofiejb@gmail.com/Min disk/Colab Notebooks/NPD relinquishment reports - 30-12-2025')