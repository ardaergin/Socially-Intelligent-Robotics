from nltk.tokenize import sent_tokenize


def break_into_sentences(text):
    """
    Breaks text into a list of sentences.
    """
    sentences = sent_tokenize(text)
    return sentences
