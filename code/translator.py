#!/usr/bin/env python
# -*- coding: utf-8 -*-
import sys
import os
import collections
import operator
import sets
import re
import string

devFile = '../corpus/dev.txt'
testFile = '../corpus/test.txt'
dictFile = '../dic/dict.txt'

nGramForBLEU = 3


# Parses the training file given in dev.txt
# Returns a list of sentences, where each sentence is given
# as a list of the words in that sentence

# Strips all punctuation (both English and Spanish) and converts
# to lower case

def parseTrainFile(filename):
    spanishSentences = []
    englishSentences = []
    prevLine = 'English'
    f = open(filename)
    for line in f:
        if line[0] is '#': continue
        exclude = set(string.punctuation)
        sentence = ''.join(ch for ch in line if ch not in exclude)
        sentence = sentence.strip('¡¿').lower().split()
        if not sentence: continue
        if prevLine is 'English':
            spanishSentences.append(sentence)
            prevLine = 'Spanish'
        elif prevLine is 'Spanish':
            englishSentences.append(sentence)
            prevLine = 'English'
    return (spanishSentences, englishSentences)

# Parses the dictionary given in dict.txt
# Format is 'EnglishWord:SpanishWord', all lowercase
# Returns a dict of 'Spanish Word' : 'English Word'

def parseDict(filename):
    dictionary = {}
    f = open(filename)
    for line in f:
        line = line.strip('\n')
        spanishWord, englishWord = line.split(':')
        dictionary[spanishWord] = englishWord
    return dictionary

# Returns a list of lists with a direct translation from Spanish to English
# i.e. returns a sentence for which each Spanish word is replaced with its
# English translation

def directTranslate(spanishSentences, dictionary):
    translations = []
    for sentence in spanishSentences:
        translatedSentence = []
        for word in sentence:
            if word in dictionary: translatedSentence.append(dictionary[word])
            # Catches Numbers for now, might need to change this to check that it's numeric first
            else: translatedSentence.append(word)
        translations.append(translatedSentence)
    return translations

def printTranslations(spanishSentences, englishTranslations, englishSentences, bScores):
    for idx, sentence in enumerate(englishTranslations):
        print "============= New Translation ============="
        print "Translation of: ", " ".join(spanishSentences[idx])
        print "Translation: ", " ".join(sentence)
        print "Correct Translation: ", " ".join(englishSentences[idx])
        print "BLEU-", nGramForBLEU," Score: ", bScores[idx]

# Method computes the BLEU score for all Translations given in the list englishTranslations
# when compared against the correct translation given by englishSentences. Uses n-grams given
# by the input variable n.

# Returns a list of BLEU scores corresponding to the translations given in englishTranslations

def computeBLEU(englishTranslations, englishSentences, n):
    bScores = []
    for idx, sentence in enumerate(englishTranslations):
        score = min(1.0, float(len(sentence)) / float(len(englishSentences[idx])))
        for i in range(1, n+1):
            translation = englishTranslations[idx]
            correctTranslation = englishSentences[idx]
            n_gram_count = len(translation) + 1 - i
            ref_count = 0.0
            matches = {}
            for pos in range(n_gram_count):
                substr = ' '.join(translation[pos: pos+i])
                if substr in matches:
                    matches[substr] += 1.0
                    if ' '.join(correctTranslation).count(substr) >= matches[substr]:
                        ref_count += 1.0
                elif substr in ' '.join(correctTranslation):
                    ref_count += 1.0
                    matches[substr] = 1
            score *= ref_count / n_gram_count
        bScores.append(score)
    return bScores

def main():
    spanishSentences, englishSentences = parseTrainFile(devFile)
    dictionary = parseDict(dictFile)
    englishTranslations = directTranslate(spanishSentences, dictionary)
    bScores = computeBLEU(englishTranslations, englishSentences, nGramForBLEU)
    printTranslations(spanishSentences, englishTranslations, englishSentences, bScores)

# Run
main()

