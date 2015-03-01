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
from HolbrookCorpus import HolbrookCorpus
from StupidBackoffLanguageModel import StupidBackoffLanguageModel
from LaplaceBigramLanguageModel import LaplaceBigramLanguageModel
from UnigramLanguageModel import UnigramLanguageModel

# Set system for utf-8 endocding
reload(sys)
sys.setdefaultencoding("utf-8")

# Variable gives the n-gram used in computation of the BLEU score for
# each translation.
nGramForBLEU = 2

#================== Helper Methods ===================#
# Returns true if character c is a vowel, false if not
def isVowel(c):
    return c == 'a' or c == 'e' or c == 'i' or c == 'o' or c == 'u'



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
# Uses NLTK word tokenizer to parse the file.
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

        # Pre-processing strategy #1: Throw out Spanish punctuation
        raw_line = line
        line = line.strip('¡¿')

        # Tokenize word using NLTK and ignore empty lines
        sentence = nltk.word_tokenize(line)
        if not sentence:
            continue

        if prevLine is 'English':
            rawSpanishSentences.append(raw_line)
            spanishSentences.append(sentence)
            prevLine = 'Spanish'
        elif prevLine is 'Spanish':
            rawEnglishSentences.append(raw_line)
            englishSentences.append(sentence)
            prevLine = 'English'
    return (spanishSentences, englishSentences, rawEnglishSentences, rawSpanishSentences)

# Method is a baseline direct translate, simply swaps each word for the first available word
# in the dictionary

def directTranslate(spanishSentences, dictionary):
    translations = []
    for sentence in spanishSentences:
        translatedSentence = []
        for i, word in enumerate(sentence):
            if word in dictionary:
                translatedSentence.append(dictionary[word])
            elif word.lower() in dictionary:
                translatedSentence.append(dictionary[word.lower()])
            else:
                translatedSentence.append(word)
        translations.append(translatedSentence)
    return translations



# Returns a list of lists with a direct translation from Spanish to English
# i.e. returns a sentence for which each Spanish word is replaced with its
# English translation
def translate(spanishSentences, dictionary):
    translations = []

    for sentence in spanishSentences:
        translatedSentence = []

        for i, word in enumerate(sentence):
            word = word.lower()

            if word == 'lo':
                # lo que -> what, so disregard 'lo'
                if len(sentence) > i+1 and sentence[i+1] == 'que':
                    continue

            if word == 'que':
                if i == 0 or sentence[i-1] == 'lo':
                    translatedSentence.append('what')
                # Is there any way we can tell this based on the tag (gender perhaps) instead of by  the specific word?
                # This is just a very specific rule that I'm worried won't generalize well to the test set
                elif sentence[i-1] == 'persona' or sentence[i-1] == 'personas' or sentence[i-1] == 'gente':
                    translatedSentence.append('who')
                else:
                    translatedSentence.append('that')

            elif word in dictionary:
                translatedSentence.append(dictionary[word])
            else:
                translatedSentence.append(word)

        translations.append(translatedSentence)

    return translations


# Method computes the BLEU score for all Translations given
# in the list englishTranslations when compared against the
# correct translation given by englishSentences. Returns a list
# of BLEU scores corresponding to the translations given in
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

# Post-Process #3:

# Multiple words in Spanish ("un", "una") translate into "a" in english. However,
# in english, "a" should become "an" if it is followed by a word beginning with a vowel
def aConsonantCorrection(taggedEnglishTranslations):
    updatedTranslations = []

    for sentence in taggedEnglishTranslations:
        for i in range(0, len(sentence) - 1):
            word = sentence[i][0]
            nextWord = sentence[i + 1][0]

            # if word is a, check next word to see if it begins with a vowel
            if word == 'a' and isVowel(nextWord[0]):
                sentence[i] = ('an', sentence[i][1])

        updatedTranslations.append(sentence)

    return updatedTranslations

# Post-Process #5 look for 'the' in the sentence and use a StupidBackoffLanguage Model
# to determine if the sentence is more or less fluent without the 'the'
def articleCorrection(englishTranslations, englishModel):
    updatedSentences = []
    for sentence in englishTranslations:
        for idx, word in enumerate(sentence):
            if word == 'the':
                if englishModel.score(sentence) < englishModel.score(sentence[0:idx]+sentence[idx+1:len(sentence)]):
                    del sentence[idx]
        updatedSentences.append(sentence)

    return updatedSentences


# Post-Process #4

def capitalizeFirstWord(englishTranslations):
    updatedTranslations = []

    for sentence in englishTranslations:
        if len(sentence) > 0:
            sentence[0] = sentence[0].capitalize()
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

    # TODO: Need to create HolbrookCorpus Class using HolbrookCorpus.txt
    trainPath = '../data/holbrook-tagged-train.dat'
    trainingCorpus = HolbrookCorpus(trainPath)
#    englishModel = StupidBackoffLanguageModel(trainingCorpus)
    englishModel = LaplaceBigramLanguageModel(trainingCorpus)
#    englishModel = UnigramLanguageModel(trainingCorpus)

    dictionary = parseDict(dictFile)
    spanishSentences, englishSentences, rawEnglishSentences, rawSpanishSentences = parseTrainFile(translateFile)

    # Pre-processing methods
    taggedSpanishSentences = spanishPosTag(spanishTagger, spanishSentences)

    taggedSpanishSentences = spanishNounAdjectiveSwap(taggedSpanishSentences)

    modifiedSpanishSentences = spanishUnPosTag(taggedSpanishSentences)

    # Direct Translation
    directEnglishTranslations = directTranslate(spanishSentences, dictionary)
    directTranslationBScores = computeBLEU(directEnglishTranslations, englishSentences)

    englishTranslations = translate(modifiedSpanishSentences, dictionary)


    # Post-processing methods
    taggedEnglishTranslations = posTagTranslations(englishTranslations)

    # taggedEnglishTranslations = nounAdjectiveSwap(taggedEnglishTranslations)
    taggedEnglishTranslations = verbNegation(taggedEnglishTranslations)
    taggedEnglishTranslations = aConsonantCorrection(taggedEnglishTranslations)

    englishTranslations = unPosTagTranslations(taggedEnglishTranslations)

    englishTranslations = articleCorrection(englishTranslations, englishModel)
    englishTranslations = capitalizeFirstWord(englishTranslations)

    # Scoring
    bScores = computeBLEU(englishTranslations, englishSentences)
    printTranslations(spanishSentences, englishTranslations, englishSentences, directEnglishTranslations, rawEnglishSentences, rawSpanishSentences, bScores, directTranslationBScores, taggedEnglishTranslations)


if __name__ == '__main__':
    main()
