import os
import string
from nltk.probability import FreqDist
from nltk.corpus import stopwords

with open("my_tools/stopwords.txt") as f:
    STOPWORDS = [line.strip() for line in f.readlines()]
PUNCT = set(string.punctuation)

class TextProcessor():

    @staticmethod
    def clean_tokens(tokens, remove_stopwords=False, remove_punct=False):
        cleaned = []

        for token in tokens:
            if remove_punct and all(ch in string.punctuation for ch in token): 
                continue
            if remove_stopwords and token.lower() in STOPWORDS: 
                continue
            cleaned.append(token)
        return cleaned

    @staticmethod
    def concordance(tokens, target, width=5):
        pass

    @staticmethod
    def ngrams(tokens, target, n):
        pass

    @staticmethod
    def freq_dist(tokens):
        return FreqDist(tokens)
    
    @staticmethod
    def token_freq(tokens, target):
        return tokens.count(target)

    # metode for å hente lokalisere alle tekster i en path
#    def extract_text_from_pdfs(self, folder_path): 
#        corpus = {} 
#        for filename in os.listdir(folder_path): 
#            if filename.lower().endswith(".pdf"): 
#                file_path = os.path.join(folder_path, filename) 
#                try: 
#                    text = self.text_extractor.extract_pdf_text(file_path) 
#                    corpus[filename] = text 
#                except Exception as e: 
#                    #st.error(f"Feil ved lesing av {filename}: {e}") 
#                    print(f"Feil ved lesing av {filename}: {e}")
#        self.corpus = corpus
#        return

    # metode for å lage konkordanse linjer

    # metode for å gjøre kollokasjoner

    # metode for å hente ut frekvenser

    # metode for å hente ut n-grams

if __name__ == "__main__":
    tp = TextProcessor()
    tp.extract_text_from_pdfs("Corpus/raw_data/")