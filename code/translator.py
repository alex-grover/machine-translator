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

from spanishTagger import SpanishTagger

# Set system for utf-8 endocding
reload(sys)
sys.setdefaultencoding("utf-8")

# Variable gives the n-gram used in computation of the BLEU score for
# each translation.
nGramForBLEU = 2


# Parses the dictionary passed in.
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


# Parses the training file passed in. Returns a list of sentences,
# where each sentence is given as a list of the words in that sentence.
# Strips all punctuation (both English and Spanish) and converts to
# lower case.
def parseTrainFile(filename):
    spanishSentences = []
    englishSentences = []
    rawEnglishSentences = []
    rawSpanishSentences = []
    prevLine = 'English'

    f = open(filename)
    for line in f:
        # Ignore comments
        if line[0] is '#':
            continue

        # Tokenize word using NLTK and ignore empty lines
        sentence = nltk.word_tokenize(line)
        if not sentence:
            continue

        raw_line = line

        # Pre-processing strategy #1: Throw out Spanish punctuation
        line = line.strip('¡¿')

        if prevLine is 'English':
            rawSpanishSentences.append(raw_line)
            spanishSentences.append(sentence)
            prevLine = 'Spanish'
        elif prevLine is 'Spanish':
            rawEnglishSentences.append(raw_line)
            englishSentences.append(sentence)
            prevLine = 'English'
    return (spanishSentences, englishSentences, rawEnglishSentences, rawSpanishSentences)


# Returns a list of lists with a direct translation from Spanish to English
# i.e. returns a sentence for which each Spanish word is replaced with its
# English translation
def directTranslate(spanishSentences, dictionary):
    translations = []

    for sentence in spanishSentences:
        translatedSentence = []

        for word in sentence:
            word = word.lower()
            if word in dictionary:
                translatedSentence.append(dictionary[word])
            else:
                translatedSentence.append(word)

        translations.append(translatedSentence)

    return translations


# Method computes the BLEU score for all Translations given
# in the list englishTranslations when compared against the
# correct translation given by englishSentences. Returns a list
# of BLEU scores corresponding to the translations given in\
# englishTranslations.
def computeBLEU(englishTranslations, englishSentences):
    bScores = []
    for i, sentence in enumerate(englishTranslations):
        score = min(1.0, float(len(sentence)) / float(len(englishSentences[i])))

        for j in range(1, nGramForBLEU + 1):
            translation = englishTranslations[i]
            correctTranslation = englishSentences[i]
            n_gram_count = len(translation) + 1 - j
            ref_count = 0.0
            matches = {}

            for pos in range(n_gram_count):
                substr = ' '.join(translation[pos: pos+j])

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


# ============= Pre-Processing Methods ============== #

# Pre-Process #1:

# Method looks for any nouns followed by adjectives in the Spanish
# and swaps them unless it's following a verb because we noticed that it
# is the one case where we actually don't want to swap them.

def spanishNounAdjectiveSwap(taggedSpanishSentences):
    updatedSentences = []

    for sentence in taggedSpanishSentences:
        prev = False

        for i in xrange(1, len(sentence)):
            # Check if previous word was swapped, i.e. the word
            # I'm looking at was just swapped into this position
            if prev:
                prev = False
                continue

            # Check if Adjective (JJ) is following a noun (NN)
            if sentence[i-1][1] and sentence[i][1] and sentence[i - 1][1][0] == 'n' and sentence[i][1][0] == 'a':
                # If it's following a verb, don't swap
                if sentence[i - 2] and sentence[i-2][1] and sentence[i - 2][1][0] == 'v':
                    continue

                # Otherwise, swap the two words
                print "Swapping Adjective-Noun in Spanish in: ", sentence
                swapWord = sentence[i - 1]
                sentence[i - 1] = sentence[i]
                sentence[i] = swapWord
                prev = True

        updatedSentences.append(sentence)

    return updatedSentences


# =================================================== #

# ============ Post-Processing Methods ============== #

# Post-Process #1:

# Method looks for any nouns followed by adjectives in the translation
# and swaps them unless it's following a verb because we noticed that it
# is the one case where we actually don't want to swap them. No
# occurences in our dev set of a noun followed by an adjective and not
# preceded by a verb, so it didn't end up improving performance on our
# dev set. May help improve accuracy for other cases.
def nounAdjectiveSwap(taggedEnglishTranslations):
    updatedTranslations = []

    for sentence in taggedEnglishTranslations:
        prev = False

        for i in xrange(1, len(sentence)):
            # Check if previous word was swapped, i.e. the word
            # I'm looking at was just swapped into this position
            if prev:
                prev = False
                continue

            # Check if Adjective (JJ) is following a noun (NN)
            if 'NN' in sentence[i - 1][1] and 'JJ' in sentence[i][1]:
                # If it's following a verb, don't swap
                if sentence[i - 2] and 'VB' in sentence[i - 2][1]:
                    continue

                # Otherwise, swap the two words
                swapWord = sentence[i - 1]
                sentence[i - 1] = sentence[i]
                sentence[i] = swapWord
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

        for i in range(1, len(sentence)):
            # Check if previous word was swapped, i.e. the word
            # I'm looking at was just swapped into this position
            if prev:
                prev = False
                continue

            # Check if 'no' is following a verb
            if 'no' == sentence[i - 1][0] and \
                ('VB' in sentence[i][1] or 'MD' in sentence[i][1]):
                    swap = sentence[i - 1]
                    sentence[i - 1] = sentence[i]
                    sentence[i] = ('not', swap[1])
                    prev = True

        updatedTranslations.append(sentence)

    return updatedTranslations


# =================================================== #


def spanishPosTag(spanishTagger, spanishSentences):
    posTaggedSentences = []
    for sentence in spanishSentences:
        posTaggedSentences.append(spanishTagger.tagSentence(sentence))
        print 'Spanish Tagged Sentence: ', posTaggedSentences[-1]
    return posTaggedSentences
 
def spanishUnPosTag(spanishTagSentences):
    spanishSentences = []
    for tagged_sentence in spanishTagSentences:
        sentence = []
        for word, tag in tagged_sentence:
            sentence.append(word)
        spanishSentences.append(sentence)
    return spanishSentences

       

# Method takes a list of English Translation sentences and
# returns a POS tagged sentence.
def posTagTranslations(englishTranslations):
    pos_tagged_translations = []

    for sentence in englishTranslations:
        pos_tagged_translations.append(nltk.pos_tag(sentence))

    return pos_tagged_translations


# Method takes a list of POS tagged sentences and returns a
# list of normal translated sentences
def unPosTagTranslations(taggedEnglishTranslations):
    englishTranslations = []
    for tagged_sentence in taggedEnglishTranslations:
        sentence = []
        for word, tag in tagged_sentence:
            sentence.append(word)
        englishTranslations.append(sentence)
    return englishTranslations


# Method walks through each transation and prints the Spanish
# sentence, the machine translation and the correct translation
# as well as the BLEU score of the translation.
def printTranslations(spanishSentences, englishTranslations, englishSentences, directEnglishTranslations, rawEnglishTranslations, rawSpanishSentences, bScores, directTranslationBScores, taggedEnglishTranslations):
    print "\n\n"
    print "================ TRANSLATIONS =================="
    print "\n\n"
    for i, sentence in enumerate(englishTranslations):
        print
        print "============= New Translation: {0} =============".format(i + 1)
        print "Translation of: ", " ".join(spanishSentences[i])
        print "Translation: ", " ".join(sentence)
        print "Correct Translation: ", " ".join(englishSentences[i])
        print "Raw Spanish Sentence: ", rawSpanishSentences[i]
        print "Raw Correct Translation: ", rawEnglishTranslations[i]
        print "Direct Translation: ", " ".join(directEnglishTranslations[i])
        print "Direct Translation BLEU-", nGramForBLEU," Score: ", directTranslationBScores[i]
        print "Final BLEU-", nGramForBLEU," Score: ", bScores[i]
        print "Tagged Translation: ", taggedEnglishTranslations[i]
    print "Summary: "
    for i in range(len(englishTranslations)):
        print "Sentence: ", i+1, " Direct Translation Score: ", directTranslationBScores[i], " vs. Final Score: ", bScores[i]

def main():
    if len(sys.argv) != 3:
        print "Usage: python translator.py [dictFile] [translateFile]"
        sys.exit(1)

    dictFile = sys.argv[1]
    translateFile = sys.argv[2]

    spanishTagger = SpanishTagger()

    dictionary = parseDict(dictFile)
    spanishSentences, englishSentences, rawEnglishSentences, rawSpanishSentences = parseTrainFile(translateFile)

    # Pre-processing methods
    taggedSpanishSentences = spanishPosTag(spanishTagger, spanishSentences) 

    taggedSpanishSentences = spanishNounAdjectiveSwap(taggedSpanishSentences)

    modifiedSpanishSentences = spanishUnPosTag(taggedSpanishSentences)

    # Direct Translation
    directEnglishTranslations = directTranslate(spanishSentences, dictionary)
    directTranslationBScores = computeBLEU(directEnglishTranslations, englishSentences)

    englishTranslations = directTranslate(modifiedSpanishSentences, dictionary)


    # Post-processing methods
    taggedEnglishTranslations = posTagTranslations(englishTranslations)

    taggedEnglishTranslations = nounAdjectiveSwap(taggedEnglishTranslations)
    taggedEnglishTranslations = verbNegation(taggedEnglishTranslations)

    englishTranslations = unPosTagTranslations(taggedEnglishTranslations)


    # Scoring
    bScores = computeBLEU(englishTranslations, englishSentences)
    printTranslations(spanishSentences, englishTranslations, englishSentences, directEnglishTranslations, rawEnglishSentences, rawSpanishSentences, bScores, directTranslationBScores, taggedEnglishTranslations)


if __name__ == '__main__':
    main()
