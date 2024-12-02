from nltk.tokenize import sent_tokenize
import nltk
nltk.download('punkt_tab')

def break_into_sentences(text):
    return sent_tokenize(text)
