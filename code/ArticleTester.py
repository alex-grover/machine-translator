import math, collections

class ArticleTester:

    def __init__(self, corpus):
        self.unigramCounts = collections.defaultdict(lambda: 0.0)
        self.bigramCounts = collections.defaultdict(lambda: 0.0)
        self.train(corpus)

    def train(self, corpus):
        for sentence in corpus.corpus:
            previousWord = None
            for datum in sentence.data:
                token = datum.word
                self.unigramCounts[token] += 1.0
                if previousWord != None:
                    self.bigramCounts[(previousWord, token)] += 1.0

    def score(self, pair):
        score = 0.0
        if pair[0] != 'the' or len(pair) != 2: return score
        else:
            count = self.bigramCounts[(pair[0], pair[1])]
            score = (count + 1.0) / (self.unigramCounts[pair[1]] + 1.0)
        return score
        
