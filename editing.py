import pyaudio
import wave
import sys
import audioop
import os
import math
from spectrograph import get_formants

def remove_surround(path):
    # converts the base phonetic osund records from online to the sound files 
    # I need to use in the program 
    print(path)
    if(path == "phonetic sounds/.DS_Store"):
        return
    chunk = 1024
    wf = wave.open(path, 'rb')
    p = pyaudio.PyAudio()
    
    data = wf.readframes(chunk)

    frames = []
    while data != '':
        data = wf.readframes(chunk)
        frames.append(data)

    stopstreaming = None
    streamcount = 0
    temp = []

    for i in range(len(frames)):
        if(abs(audioop.avg(frames[i], 2)) > 10):
            temp.append(frames[i])
            stopstreaming = True
        elif stopstreaming:
            if(streamcount == 32):
                break
            else: streamcount += 1

    p.terminate()
    FORMAT = pyaudio.paInt16
    CHANNELS = 2
    RATE = 44100

    filename = "new phonetic sounds/" + path[16:-4]
    waveFile = wave.open("%s new.wav" % filename, 'wb')
    waveFile.setnchannels(CHANNELS)
    waveFile.setsampwidth(p.get_sample_size(FORMAT))
    waveFile.setframerate(RATE)
    waveFile.writeframes(b''.join(temp))

def audio_compare(human, phonetic):
    # compares the human audio file to the base phonetic sound and finds the 
    # best match 
    frames = []
    chunk = int(1024/4)

    if(type(human) == str):
        wf = wave.open(human, 'rb')
        data = wf.readframes(chunk)

        while str(data) != "b''":
            data = wf.readframes(chunk)
            if(abs(audioop.avg(data, 2)) > 10):
                frames.append(data)


    else:
        for i in range(len(human)):
            if(abs(audioop.avg(human[i], 2)) > 10):
                frames.append(human[i])

    play_sound(frames)
    p = pyaudio.PyAudio()

    formants = get_formants(phonetic)
    distance = None
    start_hold = 0
    end_hold = 0

    for start in range(len(frames)):
        for end in range(start, len(frames)):
            if(abs(start - end) >= 20 and abs(start - end) < 35):
                formants_hold = get_formants(frames[start:end])
                distance_hold = get_distance(formants_hold, formants)
                if(distance == None or distance_hold < distance):
                    distance = distance_hold
                    start_hold = start
                    end_hold = end

    print(distance)
    p.terminate()
    print(start_hold, end_hold)
    return frames[start_hold:end_hold]

def save(frames, name):
    # saves file to the path name
    p = pyaudio.PyAudio()
    FORMAT = pyaudio.paInt16
    CHANNELS = 2
    RATE = 44100

    waveFile = wave.open(name, 'wb')
    waveFile.setnchannels(CHANNELS)
    waveFile.setsampwidth(p.get_sample_size(FORMAT))
    waveFile.setframerate(RATE)
    waveFile.writeframes(b''.join(frames))
    waveFile.close()

def get_distance(formants1, formants2):
    # gets the distance between the two formants
    distance = 0
    for formant in range(len(formants1)):
        try:
            distance += abs(formants1[formant] - formants2[formant])
        except:
            continue

    return distance

def record():
    # records a new file
    RECORD_SECONDS = 2

    audio = pyaudio.PyAudio()
 
    # start Recording
    stream = audio.open(format=pyaudio.paInt16, channels=2,
        rate=44100, input=True, frames_per_buffer=1024//4)

    frames = [] 
 
    for i in range(0, int(44100 / (1024//4) * RECORD_SECONDS)):
        value = stream.read(1024//4)
        frames.append(value) 
 

    # stop Recording
    stream.stop_stream()
    stream.close()
    audio.terminate()

    return frames

def play_sound(data):
    # plays a sound
    width = 2

    p = pyaudio.PyAudio()

    stream = p.open(format=p.get_format_from_width(width),
                    channels=2,
                    rate=44100,
                    input=True,
                    output=True,
                    frames_per_buffer=1024//4)

    for i in range(len(data)):
        stream.write(data[i], 1024//4)

    stream.stop_stream()
    stream.close()
    p.terminate()

# frames = record()
# play_sound(frames)
# new_frames = audio_compare(frames, os.getcwd() + "/phonetic sounds/%s.wav" % "aɪ")
# play_sound(new_frames)













