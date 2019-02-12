#!/usr/bin/env python2
# -*- coding: utf-8 -*-
"""
Created on Tue Jan 22 12:16:23 2019

@author: PE4WJ
"""

import math
import wave
import struct


#morse code dictionary
morse = {'A': '.-',     'B': '-...',   'C': '-.-.', 
        'D': '-..',    'E': '.',      'F': '..-.',
        'G': '--.',    'H': '....',   'I': '..',
        'J': '.---',   'K': '-.-',    'L': '.-..',
        'M': '--',     'N': '-.',     'O': '---',
        'P': '.--.',   'Q': '--.-',   'R': '.-.',
     	'S': '...',    'T': '-',      'U': '..-',
        'V': '...-',   'W': '.--',    'X': '-..-',
        'Y': '-.--',   'Z': '--..',
        
        '0': '-----',  '1': '.----',  '2': '..---',
        '3': '...--',  '4': '....-',  '5': '.....',
        '6': '-....',  '7': '--...',  '8': '---..',
        '9': '----.',  '*': '*'
        }

#INPUT PARAMETERS

#audio sample rate
samplerate = 44100 #samples/s

#CW tone frequency
frequency = 600 #Hz

#morse speed in words per minute
wpm = 16


#raised cosine in time rampup / rampdown
def ramp(idx, nsteps, up):
    if up: #ramp up
        phi = math.pi*(1+float(idx)/float(nsteps))
    else: #rampdown
        phi = math.pi*(2+float(idx)/float(nsteps))
    ramp = 0.5*(1+math.cos(phi))
    
    return ramp
        

#generate an array containing the oversampled CW beacon
def generatecw(str_in):
    cwarray =[]
    #number of words per minute is determined based on the word "PARIS"
    #this word contains 50 time units. So one word is 50 time units.
    cw_key_freq = (50.0/60.0)*wpm #Hz - time unit per second (so dots per second)
    oversampling = int(samplerate / cw_key_freq)

    #fraction of the duration of a dot (time unit) that is spent on rampup / 
    #a rampfraction of 0.1 means that 0.1*time_unit is used for rampup, and 0.1*time_unit for rampdown
    rampfraction = 0.1
    
    #morse code timing definition
    time_unit = 1
    dot_duration = 1*time_unit
    dash_duration = 3*time_unit
    interdotdashspacing = 1*time_unit
    intercharacterspacing = 3*time_unit
    interwordspacing = 7*time_unit
    tone_duration = 60*time_unit
    
    rampduration = int(time_unit*oversampling*rampfraction)
    dotconstantduration = dot_duration*oversampling - 2*rampduration
    dashconstantduration = dash_duration*oversampling - 2*rampduration
    toneconstantduration = tone_duration*oversampling - 2*rampduration
    
    for char in str_in:
        if char == ' ':
            for i in range(0,interwordspacing*oversampling):
                cwarray.append(0)
        else:
            #look up morse characters in the dictionary
            dotsdashes = morse[char.upper()]
            for dotdash in dotsdashes:
                if dotdash == '.':
                    #dot
                    #rampup
                    for i in range(0,rampduration):
                        cwarray.append(ramp(i,rampduration,True))
                    #constant level
                    for i in range(0,dotconstantduration):
                        cwarray.append(1)
                    #rampdown
                    for i in range(0,rampduration):
                        cwarray.append(ramp(i,rampduration,False))
                    
                elif dotdash == '-':
                    #dash
                    #rampup
                    for i in range(0,rampduration):
                        cwarray.append(ramp(i,rampduration,True))
                    #constant level
                    for i in range(0,dashconstantduration):
                        cwarray.append(1)
                    #rampdown
                    for i in range(0,rampduration):
                        cwarray.append(ramp(i,rampduration,False))

                elif dotdash == '*': #special case for continuous tone (microwave beacon-like)
                    #dash
                    #rampup
                    for i in range(0,rampduration):
                        cwarray.append(ramp(i,rampduration,True))
                    #constant level
                    for i in range(0,toneconstantduration):
                        cwarray.append(1)
                    #rampdown
                    for i in range(0,rampduration):
                        cwarray.append(ramp(i,rampduration,False))
                        
                #inter dot-dash spacing
                for i in range(0,interdotdashspacing*oversampling):
                    cwarray.append(0)
                    
            #inter character spacing
        for i in range(0,intercharacterspacing*oversampling):
            cwarray.append(0)
        
    return cwarray                          
  

def modulate(cw_array_in):
    #generate sine wave and multiply with CW samples

    normalized_freq = float(frequency)/float(samplerate)
    phase = []
    modulated_out = []
    #NCO
    theta = 0
    for idx in range(0, len(cw_array_in)):
        #phase accumulator
        theta += 2*math.pi*normalized_freq
        phase.append(theta)
        #wrap phase
        theta % 2*math.pi
        #take the since of the phase to generate our "LO"
        sine = math.sin(theta)
        
        #multiply input CW samples by a sine wave (the actual modulation process)
        modulated_out.append(sine*cw_array_in[idx])
    
    return modulated_out

        
def generate_wav(modulated_in):
    #write generated beacon to wave file
    filename = 'cwbeacon.wav'
    #Open wav file
    wavfile=wave.open(filename,'w')

    #wav file parameters
    nchannels = 1
    sampwidth = 2
    
    #determine the amount of frames in the wav file
    nframes = len(modulated_in)
    
    #set parameters related to compression (no compression used)
    comptype = 'NONE'
    compname = 'not compressed'
    
    #set wav file parameters
    wavfile.setparams((nchannels, sampwidth, samplerate, nframes, comptype, compname))

    #write samples to wav file
    for sample in modulated_in:
        wavfile.writeframes(struct.pack('h', int( sample * 32767.0 )))
    #close the wav file
    wavfile.close()

    return   


#generate the actual beacon wav file
beacon = 'NOCALL JO99 *  '
generate_wav(modulate(generatecw(beacon)))