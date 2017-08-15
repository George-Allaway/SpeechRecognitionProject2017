#!/usr/bin/env python2
# -*- coding: utf-8 -*-
"""
Created on Tue Aug 15 20:14:54 2017

@author: George
"""

"""
Python script to run the experiment form including Adaptive staircase using 
speech recognition to process responses.
"""

import numpy as np
import sounddevice as sd
import scipy.io.wavfile as sio
import wave
import os
import speech_recognition as sr
import pandas as pd
from time import sleep, localtime

r = sr.Recognizer()
def Google_SR(audio):
        # recognize speech using Google Speech Recognition
    try:
        recognition = r.recognize_google(audio)
        return recognition
    except sr.UnknownValueError:
        return "Google Cloud Speech could not understand audio"
    except sr.RequestError as e:
        return "Could not request results from Google Cloud Speech service"
            
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
    return transcription

def AddNoiseCaliCurve(Target,Babble,SNR):
    lenTarg = len(Target)
    insert_point = int(2.5*44100)
    SPL = 80
    a = 0.049
    b = 5.6
    logrmsVAL = a*SPL+b
    rmsVAL = np.power(10.,logrmsVAL)
    Target *= rmsVAL
    logrmsNOISE = logrmsVAL - a*SNR
    rmsNOISE = np.power(10.,logrmsNOISE)
    Babble *= rmsNOISE
    Babble[insert_point:insert_point+lenTarg] = Babble[insert_point:insert_point+lenTarg] + Target
    Babble /= Babble.max()
    return Babble

def GenerateData(FILENAME):
	soundfile = wave.open(FILENAME)
	num_Channels = soundfile.getnchannels()
	if num_Channels == 1:
		Fs, Sig = sio.read(FILENAME)
		return Fs, Sig
	elif num_Channels == 2:
		Fs, Sig = sio.read(FILENAME)
		Sig_Len = len(Sig)
		New_Sig = np.zeros(shape = Sig_Len)
		for i in range(0,Sig_Len):
			New_Sig[i] = ((Sig[i][0]+Sig[i][1])/2)
		return Fs, New_Sig

def PlayBack(Signal,Fs):
    sd.play(Signal,Fs,blocking = True)
    
def RMS(Signal):
	return np.sqrt(np.mean(np.square(Signal)))

def Keyword_Match2(transc,Real_sentence): 
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
	return numwords/float(rlength)


def TrackRUN(SNR,p,stepsize,Score,phase):
    delta = np.empty((1))
    for track in range(0,1):
        if Score >= 0.5:
            delta[track] = -1*stepsize[phase]
        elif Score < 0.5:
            delta[track] = +1*(stepsize[phase]*((1-p)/p))        
    sumdelta = sum(delta)
    if np.sign(sumdelta) == -1.0:
		# negative sumdelta means SNR is decreasing, due to positive response
        direction = 1
    elif np.sign(sumdelta) == 1.0:
		# positive sumdelta measn that SNR is increasign due to negative response
        direction = 0
    newSNR = SNR + sumdelta
    return direction,newSNR,sumdelta


def CreatingNoise(SNR,targetNUM):
    babbleNUM = np.random.randint(1,100)
    babblePATH = "/Users/George/Documents/CurrentProjectFiles/OpenSesameExpAMY09_08_17/BabbleTracks"
    babbleFILE = "babble%d.wav" %babbleNUM
    babbleFILENAME = os.path.join(babblePATH,babbleFILE)
    FsB, Babble = GenerateData(babbleFILENAME)
    Babble = Babble.astype('float64')/32767
    Babble = Babble/float(RMS(Babble))
    targetPATH = "/Users/George/Documents/CurrentProjectFiles/OpenSesameExpAMY09_08_17/Amy"
    FILEid = '{:03}'.format(targetNUM)
    targetFILE = "test_sentences_%s.wav" %FILEid
    targetFILENAME = os.path.join(targetPATH,targetFILE)
    FsT, Target = GenerateData(targetFILENAME)
    Target = Target.astype('float64')/32767
    Target = Target/float(RMS(Target))
    MaskedNoise = AddNoiseCaliCurve(Target,Babble,SNR)
    return MaskedNoise,FsT
  

def Record(Fs,TRACK,expFOLDER):    
    duration = 7*Fs
    print "Begin Recording"
    recording = sd.rec(duration,samplerate = Fs,blocking = True,channels = 2, dtype = 'int16')
    SAVEPATH = expFOLDER
    SAVE_NAME = "Track%d.wav" %TRACK
    SAVEFILE = os.path.join(SAVEPATH,SAVE_NAME)
    sio.write(SAVEFILE,Fs,recording)
    return SAVEFILE
    
      
def MAKEDATAFRAME():
    columns = ['Trial Number','Track Number','SNR','Real Sentence','Transcribed Sentence',
               'Score','SNR Change','SNR of Reversals','direction','Final Result']
    Results = pd.DataFrame(index = None, columns = columns)
    return Results
    
   
def TrialRUN2(p,startTrack,endTrack,expFOLDER):
    initSNR = 10
    SNR = 10
    stepsizes = [2,0.75]
    numReversals = [2,5]
    phase = 0
    trackNUM = 0
    numRevs = 0
    direction = 1
    #direction - 1 corresponds to a positive result, 0 to a negative result.
    SNR_Reversals =[]
    loopFILE = "/Users/George/Documents/CurrentProjectFiles/AdaptiveStaircase/LoopTableAdaptive.csv" 
    loopTABLE = pd.read_csv(loopFILE)
    Results = MAKEDATAFRAME()
    targetTRACKS = np.arange(startTrack,endTrack+1)
    np.random.shuffle(targetTRACKS)

    while numRevs < numReversals[phase] and trackNUM < endTrack:
        print
        print "Trial number: %d" %trackNUM
        print
        print "SNR: %d" %SNR
        TRACK = targetTRACKS[trackNUM]
        if trackNUM == 0:
            Stimuli, Fs = CreatingNoise(initSNR,TRACK)
        else:
            Stimuli, Fs = CreatingNoise(SNR,TRACK)
        print
        print "AUDIO PLAYING"
        print
        PlayBack(Stimuli,Fs)
        print
        print "PREPARE TO RECORD"
        sleep(3)
        SAVEFILE = Record(Fs,TRACK,expFOLDER)
        print "Recording Finished"
        transcription = AudioFileTranscribe(SAVEFILE)
        print "Transcription: %s" %(transcription)
        realSENT = loopTABLE['Real_Sentence'][TRACK-1]
        if transcription == "Google Cloud Speech could not understand audio":
            Score = 0
        elif transcription == "Could not request results from Google Cloud Speech service":
            Score = 0
        else:
            Score = Keyword_Match2(transcription,realSENT)
        print "Score: %0.3f" %Score
        newdirection, newSNR, SNRChange = TrackRUN(SNR,p,stepsizes,Score,phase)
        if newdirection != direction:
            numRevs += 1
            SNR_Reversals.append(SNR)
        else:
            numRevs = numRevs
#        Save stuff
        print
        print "numRevs: %d" %numRevs
        print "phase: %d" %phase
        print "number of reversals: %d" %numReversals[phase]
        print
        Results.set_value(TRACK,'Real Sentence',realSENT)
        Results.set_value(TRACK,'SNR',SNR)
        Results.set_value(TRACK,'newSNR',newSNR)
        Results.set_value(TRACK,'direction',direction)
        Results.set_value(TRACK,'Transcribed Sentence',transcription)
        Results.set_value(TRACK,'Trial Number',trackNUM)
        Results.set_value(TRACK,'Track Number',TRACK)
        Results.set_value(TRACK,'SNR of Reversals',SNR_Reversals)
        Results.set_value(TRACK,'SNR Change',SNRChange)
        Results.set_value(TRACK,'Score',Score)
        if SNR >= initSNR:
            numRevs = 0
        if phase == 0 and numRevs == numReversals[phase]:
            phase = 1
            numRevs = 0
#        Update Variables for next track
        SNR = newSNR
        trackNUM += 1
        direction = newdirection
    finalRESULT = np.mean(SNR_Reversals[-3:])
    Results.set_value(TRACK,'final result',finalRESULT)
    return Results

def main():
    times = localtime()
    year = times.tm_year
    month = times.tm_mon
    day = times.tm_mday
    hour= times.tm_hour
    minute = times.tm_min
#    p = float(raw_input("enter your threshold: "))
#    start = int(raw_input("enter your starting sentence number: "))
#    end = int(raw_input("enter your ending sentence number: "))
    subject_number = int(raw_input("Enter Subject number: "))
    expFOLDER = "SubjectNR_%d_DATE_%d_%d_%d_%d_%d" %(subject_number,day,month,year,hour,minute)
    os.makedirs(expFOLDER)
    print "%%%%%%%%%%% WELCOME TO EXPERIMENT %%%%%%%%%%%"
    print
    print "Experiment begins now..."
    Results = TrialRUN2(0.5,1,31,expFOLDER)
    SavingNAME = "Results_SubjectNumber%d.csv" %subject_number
    SAVE = os.path.join(expFOLDER,SavingNAME)
    Results.to_csv(SAVE,index = False)
    

main()
    
    

    
            
        
        
            
        
        
        
        
        

        
        
        
        
    
