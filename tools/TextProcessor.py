# lag en klasse som bruker spacy til å prosessere tekster. 
# vurder å lage et plaintextcorpus
import spacy
import os
import TextExtractor

class TextProcessor():
    def __init__(self):
        self.pipe = spacy.load(("en_core_news_sm"))

        # vurder å bruke corpus-klassen fra spacy
        self.corpus = None
        self.corpus_path = None
        pass

    # metode for å hente lokalisere alle tekster i en path
    def extract_text_from_pdfs(folder_path): 
        corpus = {} 
        for filename in os.listdir(folder_path): 
            if filename.lower().endswith(".pdf"): 
                file_path = os.path.join(folder_path, filename) 
                try: 
                    text = extract_text(file_path) 
                    corpus[filename] = text 
                except Exception as e: 
                    st.error(f"Feil ved lesing av {filename}: {e}") 
        return corpus

    # metode for å lage konkordanse linjer

    # metode for å gjøre kollokasjoner

    # metode for å hente ut frekvenser

    # metode for å hente ut n-grams