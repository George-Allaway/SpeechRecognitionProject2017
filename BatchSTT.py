#!/usr/bin/env python2
# -*- coding: utf-8 -*-
"""
Created on Sun Aug 13 19:07:15 2017

@author: George
"""

"""
Batch processing of audio (WAV) files for speech to text. 
user will input a batch of audio files and a list of sentences output will be a
list of transcriptions and a keyword match.
"""
# Dependencies

import speech_recognition as sr
import pandas as pd
import os

def Keyword_Match(transc,Real_sentence):
    transc = transc.lower()
    STT_split = transc.split()
    Real_sent = Real_sentence.lower()
    Real_split = Real_sent.split()
    rlength = len(Real_split)
    numwords = 0
    for i in Real_split:
        for j in STT_split:
            if i == j:
                STT_split.remove(j)
                numwords += 1
                break
    print numwords
    return numwords/float(rlength)

def Google_SR(audio):
        # recognize speech using Google Speech Recognition
    try:
        recognition = r.recognize_google(audio)
        return recognition
    except sr.UnknownValueError:
        print("Google Cloud Speech could not understand audio")
    except sr.RequestError as e:
        print("Could not request results from Google Cloud Speech service; {0}".format(e))
    
def AudioFileTranscribe(FILENAME):
    """
    
    AudioFileTranscribe: Transcribes audio from a WAV file and 
    returns and prints the transcription to terminal
    
    FILENAME: local or system path to file as a string including file format
    e.g. .wav
    
    """
    with sr.AudioFile(FILENAME) as source:
        audio = r.record(source) 
    transcription = Google_SR(audio)
#    print "You Said: %s" %transcription
    return transcription 

def BatchTranscribe(FILEPATH,sentenceFILE,numSent):
    Transcriptions = {}
    Score = {}
    Sentences = CreateSentDict(sentenceFILE)
    for i in range(1,numSent+1):
        FILENAME = "test_sentences_%s.wav" %'{:03}'.format(i)
        FILE = os.path.join(FILEPATH,FILENAME)
        STT = AudioFileTranscribe(FILE)
        Transcriptions[i] = STT.lower()
        Score[i] = Keyword_Match(STT,Sentences[i])
    return Transcriptions,Score,Sentences
        
    
def CreateSentDict(sentenceFILE):
    Sentences = {}
    with open(sentenceFILE) as source:
        sents = list(source)
    for i in range(0,len(sents)):
        senten = sents[i]
        senten = senten[:-2]
        Sentences[i+1] = senten.lower()
    return Sentences
        
r = sr.Recognizer() 
sentenceFILE = "List of Sentences"
FILEPATH = "FILEPATH"
Transcriptions, Scores,Sentences = BatchTranscribe(FILEPATH,sentenceFILE,30)

columns = ['Track','Transcription','Real_Sentence','Score']
Results = pd.DataFrame(columns = columns)
for i in range(1,31):
    Results.set_value(i,'Track',i)
    Results.set_value(i,'Real_Sentence',Sentences[i])
    Results.set_value(i,'Transcription',Transcriptions[i])
    Results.set_value(i,'Score',Scores[i])

Results.to_csv("Results.csv",index = False)





