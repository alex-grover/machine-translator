#!/usr/bin/env python
# -*- coding: utf-8 -*-
import sys
import os
import collections
import operator
import sets
import re
import string
import nltk

# Set system for utf-8 endocding
reload(sys)
sys.setdefaultencoding("utf-8")

# ======== GLOBALS ==========
devFile = '../corpus/dev.txt'
testFile = '../corpus/test.txt'
dictFile = '../dic/dict.txt'

# Variable gives the n-gram used in computation of the BLEU score for
# each translation
nGramForBLEU = 3

# ==========================


# Parses the training file given in dev.txt
# Returns a list of sentences, where each sentence is given
# as a list of the words in that sentence

# Strips all punctuation (both English and Spanish) and converts
# to lower case

def parseTrainFile(filename):
    spanishSentences = []
    englishSentences = []
    rawEnglishSentences = []
    rawSpanishSentences = []
    prevLine = 'English'
    f = open(filename)
    for line in f:
        if line[0] is '#': continue
        raw_line = line

# Pre-processing strategy #1: Throw out Spanish punctuation
        line = line.strip('¡¿')

        sentence = nltk.word_tokenize(line)
        if not sentence: continue
        if prevLine is 'English':
            rawSpanishSentences.append(raw_line)
            spanishSentences.append(sentence)
            prevLine = 'Spanish'
        elif prevLine is 'Spanish':
            rawEnglishSentences.append(raw_line)
            englishSentences.append(sentence)
            prevLine = 'English'
    return (spanishSentences, englishSentences, rawEnglishSentences, rawSpanishSentences)

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
            elif word.lower() in dictionary: translatedSentence.append(dictionary[word.lower()])
            # Catches Numbers for now, might need to change this to check that it's numeric first
            else: translatedSentence.append(word)
        translations.append(translatedSentence)
    return translations

# ============= Pre-Processing Methods ============== #


# =================================================== #

# ============ Post-Processing Methods ============== #

# Post-Process #1:

# Method looks for any nouns followed by adjectives in the translation and swaps them
# unless it's following a verb because I noticed that it is the one case where we
# actually don't want to swap them

# No occurences in our dev set of a noun followed by an adjective and not preceded by a verb,
# so it didn't end up improving performance on our dev set

def nounAdjectiveSwap(taggedEnglishTranslations):
    updatedTranslations = []
    for sentence in taggedEnglishTranslations:
        prev = False
        for idx in range(1, len(sentence)):
            # Check if previous word was swapped, i.e. the word I'm looking at was just
            # swapped into this position
            if prev:
                prev = False
                continue
            # Check if Adjective (JJ) is following a noun (NN)
            if 'NN' in sentence[idx-1][1] and 'JJ' in sentence[idx][1]:
                # If it's following a verb, don't swap
                if sentence[idx-2] and 'VB' in sentence[idx-2][1]: continue
                # Otherwise, swap the two words
                swapWord = sentence[idx-1]
                sentence[idx-1] = sentence[idx]
                sentence[idx] = swapWord
                prev = True
        updatedTranslations.append(sentence)
    return updatedTranslations

# Post-Process #2:

# Spanish uses the negation (e.g. the word 'no') before the verb whereas
# it is used following the verb in English (e.g. 'is not')

def verbNegation(taggedEnglishTranslations):
    updatedTranslations = []
    for sentence in taggedEnglishTranslations:
        prev = False
        for idx in range(1, len(sentence)):
            # Check if previous word was swapped, i.e. the word I'm looking at was just
            # swapped into this position
            if prev:
                prev = False
                continue
            # Check if 'no' is following a verb
            if 'no' == sentence[idx-1][0] and ('VB' in sentence[idx][1] or 'MD' in sentence[idx][1]):
                swap = sentence[idx - 1]
                sentence[idx - 1] = sentence[idx]
                sentence[idx] = ('not', swap[1])
                prev = True
        updatedTranslations.append(sentence)
    return updatedTranslations



# =================================================== #

# Method takes a list of English Translation sentences and returns a POS tagged sentence

def posTagTranslations(englishTranslations):
    pos_tagged_translations = []
    for sentence in englishTranslations:
        pos_tagged_translations.append(nltk.pos_tag(sentence))
#        print "Tagged Sentence: ", pos_tagged_translations[-1]
    return pos_tagged_translations

# Method takes a list of POS tagged sentences and returns a list of normal translated
# sentences

def unPosTagTranslations(taggedEnglishTranslations):
    englishTranslations = []
    for tagged_sentence in taggedEnglishTranslations:
        sentence = []
        for word, tag in tagged_sentence:
            sentence.append(word)
        englishTranslations.append(sentence)
    return englishTranslations

# Method walks through each transation and prints the Spanish sentence, the machine translation
# and the correct translation as well as the BLEU score of the translation.

def printTranslations(spanishSentences, englishTranslations, englishSentences, rawEnglishTranslations, rawSpanishSentences, bScores, directTranslationBScores, taggedEnglishTranslations):
    print "\n\n"
    print "================ TRANSLATIONS =================="
    print "\n\n"
    for idx, sentence in enumerate(englishTranslations):
        print
        print "============= New Translation: {0} =============".format(idx + 1)
        print "Translation of: ", " ".join(spanishSentences[idx])
        print "Translation: ", " ".join(sentence)
        print "Tagged Translation: ", taggedEnglishTranslations[idx]
        print "Correct Translation: ", " ".join(englishSentences[idx])
        print "Raw Spanish Sentence: ", rawSpanishSentences[idx]
        print "Raw Correct Translation: ", rawEnglishTranslations[idx]
        print "Direct Translation BLEU-", nGramForBLEU," Score: ", directTranslationBScores[idx]
        print "Final BLEU-", nGramForBLEU," Score: ", bScores[idx]

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
                    matches[substr] += 1
                    if ' '.join(correctTranslation).count(substr) >= matches[substr]:
                        ref_count += 1.0
                elif substr in ' '.join(correctTranslation):
                    ref_count += 1.0
                    matches[substr] = 1
            score *= ref_count / n_gram_count
        bScores.append(score)
    return bScores

def main():
    spanishSentences, englishSentences, rawEnglishSentences, rawSpanishSentences = parseTrainFile(devFile)
    dictionary = parseDict(dictFile)

    # Pre-processing methods
    
    # Direct Translation
    englishTranslations = directTranslate(spanishSentences, dictionary)
    directTranslationBScores = computeBLEU(englishTranslations, englishSentences, nGramForBLEU)

    # Post-processing methods
    taggedEnglishTranslations = posTagTranslations(englishTranslations)

    taggedEnglishTranslations = nounAdjectiveSwap(taggedEnglishTranslations)
    taggedEnglishTranslations = verbNegation(taggedEnglishTranslations)
    
    englishTranslations = unPosTagTranslations(taggedEnglishTranslations)

    # Scoring
    bScores = computeBLEU(englishTranslations, englishSentences, nGramForBLEU)
    printTranslations(spanishSentences, englishTranslations, englishSentences, rawEnglishSentences, rawSpanishSentences, bScores, directTranslationBScores, taggedEnglishTranslations)

# Run
main()

