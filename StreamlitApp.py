import os
import streamlit as st
from my_tools.Corpus import Corpus
from my_tools.Document import Document
from my_tools.TextProcessor import TextProcessor

class StreamlitApp():
    def __init__(self):
        self.corpus = Corpus("Corpus/raw_data/") 
        
        self.processor = TextProcessor()

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
        if self.mode == "Frequent words":
            self.show_frequencies()
        elif self.mode == "Word frequency":
            self.show_word_frequency()

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

if __name__ == "__main__":
    StreamlitApp()