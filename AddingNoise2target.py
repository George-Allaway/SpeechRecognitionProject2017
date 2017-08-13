#!/usr/bin/env python2
# -*- coding: utf-8 -*-
"""
Created on Sat Aug 12 16:24:04 2017

@author: George
"""

"""Adding noise to target signal with calibration constants"""


from numpy import sqrt, mean,square,random, zeros,power, arange
import scipy.io.wavfile as sio
import wave
import sounddevice as sd


def RMS(Signal):
	return sqrt(mean(square(Signal)))

def GenerateData(FILENAME):
	soundfile = wave.open(FILENAME)
	num_Channels = soundfile.getnchannels()
	if num_Channels == 1:
		Fs, Sig = sio.read(FILENAME)
		return Fs, Sig
	elif num_Channels == 2:
		Fs, Sig = sio.read(FILENAME)
		Sig_Len = len(Sig)
		New_Sig = zeros(shape = Sig_Len)
		for i in range(0,Sig_Len):
			New_Sig[i] = ((Sig[i][0]+Sig[i][1])/2)
		return Fs, New_Sig

def AddNoiseCaliCurve(Target,Babble,SNR):
    lenTarg = len(Target)
    insert_point = int(2.5*44100)
    SPL = 80
    a = 0.049
    b = 5.6
    logrmsVAL = a*SPL+b
    print logrmsVAL
    rmsVAL = power(10.,logrmsVAL)
    print rmsVAL
    Target *= rmsVAL
    print RMS(Target)
    logrmsNOISE = logrmsVAL - a*SNR
    rmsNOISE = power(10.,logrmsNOISE)
    Babble *= rmsNOISE
    Babble[insert_point:insert_point+lenTarg] = Babble[insert_point:insert_point+lenTarg] + Target
    Babble /= Babble.max()
    return Babble

    
#TargetFN = "Target FilePath"
#BabbleTrack = "BabbleFilePath"
#FsT, Signal = GenerateData(TargetFN)
#Signal = Signal.astype('float64')/32767
#rmsSignal = RMS(Signal)
#Signal /= float(rmsSignal)
#print "Signal RMS: %0.5f" %RMS(Signal)
#FsB, Noise = sio.read(BabbleTrack)
#Noise = Noise.astype('float64')/32767
#rmsNoise = RMS(Noise)
#Noise /= float(rmsNoise)
#print "Noise RMS: %0.5f" %RMS(Noise)
#
#MaskedNoise = AddNoiseCaliCurve(Signal,Noise,8)
#
#sd.play(MaskedNoise,FsT,blocking = True)

SNRlist = arange(-5,6,1)
TrackNum = arange(400,411,1)
count = 0
for S in SNRlist:
    TargetFile = "TargetFileName" %TrackNum[count]
    BabNum = random.randint(1,100)
    BabbleFile = "BabbleFileName" %BabNum
    FsT, Target = GenerateData(TargetFile)
    Target = Target.astype('float64')/32767
    rmsTarget = RMS(Target)
    Target /= float(rmsTarget)
    FsB, Babble = sio.read(BabbleFile)
    Babble = Babble.astype('float64')/32767
    rmsBabble = RMS(Babble)
    Babble /= float(rmsBabble)
    MaskedNoise = AddNoiseCaliCurve(Target,Babble,S)
    SaveFile = "SaveFileName" %(TrackNum[count],S)
    sio.write(SaveFile,FsT,MaskedNoise)
    count += 1



