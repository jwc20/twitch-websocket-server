# chat_preprocessor.py
import re
import spacy


class ChatPreprocessor:
    def __init__(self):
        self.nlp = spacy.load("en_core_web_sm")

    def remove_stopwords(self, sentence):
        doc = self.nlp(sentence)
        filtered_sentence = " ".join([token.text for token in doc if not token.is_stop])
        return filtered_sentence

    # TODO: modify based on the result of the model
    def preprocess_chat_message(sentence):
        sentence = re.sub(r"@\w+", "", sentence)
        sentence = sentence.lower()
        sentence = remove_stopwords(sentence)
        sentence = re.sub("[^a-zA-z0-9\s]", "", sentence)
        sentence = re.sub(r"\b(?!69\b|420\b)\d+\b", "", sentence)
        sentence = re.sub(r"\b\w{1,3}\b", "", sentence)
        sentence = re.sub(" +", " ", sentence).strip()
        return sentence
