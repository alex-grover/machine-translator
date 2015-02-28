import math, collections

class LaplaceBigramLanguageModel:

  def __init__(self, corpus):
    """Initialize your data structures in the constructor."""
    self.bigramCounts = collections.defaultdict(lambda: 0)
    self.total = 0
    self.train(corpus)

  def train(self, corpus):
    """ Takes a corpus and trains your language model. 
        Compute any counts or other corpus statistics in this function.
    """  
    for sentence in corpus.corpus:
        previousWord = None
        for datum in sentence.data:
            token = datum.word
            if previousWord != None:
                self.bigramCounts[(previousWord,token)] = self.bigramCounts[(previousWord,token)] + 1
                self.total += 1
            previousWord = token


  def score(self, sentence):
    """ Takes a list of strings as argument and returns the log-probability of the 
        sentence using your language model. Use whatever data you computed in train() here.
    """
    score = 0.0
    previousWord = None
    for token in sentence:
        if previousWord != None:
            count = self.bigramCounts[(previousWord,token)]
            score += math.log(count+1)
            score -= math.log(self.total+len(self.bigramCounts))
        previousWord = token
    return score
