import math, collections

class CustomLanguageModel:

  def __init__(self, corpus):
    """Initialize your data structures in the constructor."""
    self.trigramCounts = collections.defaultdict(lambda: 0)
    self.bigramCounts = collections.defaultdict(lambda: 0)
    self.unigramCounts = collections.defaultdict(lambda: 0)
    self.unigramTotal = 0
    self.alpha = 0.4
    self.train(corpus)

  def train(self, corpus):
    """ Takes a corpus and trains your language model. 
        Compute any counts or other corpus statistics in this function.
    """  
    for sentence in corpus.corpus:
        holeWord = None
        previousWord = None
        for datum in sentence.data:
            token = datum.word
            self.unigramCounts[token] = self.unigramCounts[token] + 1
            self.unigramTotal += 1
            if previousWord != None:
                self.bigramCounts[(previousWord,token)] = self.bigramCounts[(previousWord, token)] + 1
                if holeWord != None:
                    self.trigramCounts[(holeWord,previousWord,token)] = self.trigramCounts[(holeWord,previousWord,token)] + 1
            holeWord = previousWord
            previousWord = token
                

  def score(self, sentence):
    """ Takes a list of strings as argument and returns the log-probability of the 
        sentence using your language model. Use whatever data you computed in train() here.
    """
    score = 0.0
    holeWord = None
    previousWord = None
    for token in sentence:
        if holeWord != None and previousWord != None and (holeWord,previousWord,token) in self.trigramCounts:
            count = self.trigramCounts[(holeWord,previousWord,token)]
            score += math.log(count)
            score -= math.log(self.bigramCounts[(holeWord,previousWord)])
        elif previousWord != None and (previousWord,token) in self.bigramCounts:
            count = self.bigramCounts[(previousWord,token)]
            score += math.log(self.alpha * count)
            score -= math.log(self.unigramCounts[previousWord])
        else:
            count = self.unigramCounts[token] + 1
            score += math.log(self.alpha * self.alpha * count)
            score -= math.log(self.unigramTotal + len(self.unigramCounts))
        holeWord = previousWord
        previousWord = token
    return score
