#!/usr/bin/env python
# -*- coding: utf-8 -*-
import sys
import os
import collections
import operator
import sets
import re
import string

devFile = 'dev.txt'
testFile = 'test.txt'
dictFile = 'dict.txt'


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
        translations.append(translatedSentence)
    return translations

def printTranslations(spanishSentences, englishTranslations, englishSentences):
    for idx, sentence in enumerate(englishTranslations):
        print "============= New Translation ============="
        print "Translation of: ", " ".join(spanishSentences[idx])
        print "Translation: ", " ".join(sentence)
        print "Correct Translation: ", " ".join(englishSentences[idx])


def main():
    spanishSentences, englishSentences = parseTrainFile(devFile)
    dictionary = parseDict(dictFile)
    englishTranslations = directTranslate(spanishSentences, dictionary)
    printTranslations(spanishSentences, englishTranslations, englishSentences)

# Run
main()

