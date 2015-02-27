from nltk.corpus import cess_esp as cess
from nltk import UnigramTagger as ut

class SpanishTagger:

    # Initialize and train unigram tagger
    def __init__(self):
        cess_cents = cess.tagged_sents()
        self.unigramTagger = ut(cess_cents)

    # Takes in sentence as a list of Spanish words, returns a tagged version
    # of the list
    def tagSentence(self, sentence):
        return self.unigramTagger.tag(sentence)
