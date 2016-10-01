from tkinter import *
import pyaudio
import wave
import audioop
from phonetics import *
from editing import *
import os
import ast
import math

# https://www.cs.cmu.edu/~112/notes/notes-animations.html
# bare bones for event baised animation taken from website

def new_sound(data):
    # records a new sound 
    RECORD_SECONDS = 2

    audio = pyaudio.PyAudio()
 
    # start Recording
    stream = audio.open(format=data.format, channels=data.channels,
        rate=data.rate, input=True, frames_per_buffer=data.chunk)

    frames = [] 

    # reads the frames
    for i in range(0, int(data.rate / data.chunk * RECORD_SECONDS)):
        value = stream.read(data.chunk)
        frames.append(value) 

    # stop Recording
    stream.stop_stream()
    stream.close()
    audio.terminate()

    # saves the saves the reorded sound to init
    data.current_recording = frames

def play_sound(data):
    # plays a sound
    width = 2

    p = pyaudio.PyAudio()

    # opens stream to start playing sound
    stream = p.open(format=p.get_format_from_width(width), 
        channels=data.channels, rate=data.rate, input=True, output=True,
        frames_per_buffer=data.chunk)

    # plays the individual frames
    for i in range(len(data.current_recording)):
        stream.write(data.current_recording[i], data.chunk)

    # stops streaming
    stream.stop_stream()
    stream.close()
    p.terminate()

def remove_white_noise(frames):
    # removes all white noice (amplitude less than 5)
    temp = []
    for i in range(len(frames)):
        if(abs(audioop.avg(frames[i], 2)) > 5):
            temp.append(frames[i])

    return temp

def make_sound(data):
    # makes sound based on frames
    data.hold = []
    data.current_recording = []
    frames = turn_to_frames(data)
    data.current_recording = frames
    play_sound(data)
    data.hold = frames

def turn_to_string(data, value = True):
    # turns typed words to string
    values = ['comma', 'period', 'question', 'slash', 'quotedbl', 'quoteright', 'colon', 'semicolon', 'underscore', 'minus', 'parenright', 'parenleft']
    values2 = [',', '.', '?', '/', '"', "'", ':', ';', '_', '-', ')', '(']

    string = ""
    for i in range(len(data)):
        # excludes the symbols that were added in (optional)
        if((data[i] in values or data[i] in values2) and value):
            continue
        string += data[i]
    return string

def find_closest_space(word, end):
    # finds the closest space value to character 45
    for place in range(end, 0, -1):
        if(word[place] == " "):
            return place

def turn_to_string2(data):
    # turns typed words to a list of strings size <45 for redraw all
    string =[]
    last = 0
    for i in range(len(data.word)):
        if(i % 45 == 0 and i != 0):
            # creates a new section of every space around 45 characters
            split = find_closest_space(data.word, i)
            string.append(turn_to_string(data.word[last: split], False))
            last = split
    # adds remaining values to the results
    string.append(turn_to_string(data.word[last:], False))
    return string

def turn_to_string3(data):
    # turns typed words into a list of strings for the added words
    hold = turn_to_string(data.word) + " "
    string = []
    current = ""
    for i in range(len(hold)):
        if hold[i] in data.values2 or hold[i] in data.values:
            # removes symbols from the typed words
            continue
        if(hold[i] == " " and len(current) > 0):
            string.append(current)
            current = ""
        elif(hold[i] != " "):
            current += hold[i]
    return string

def evaluate(data):
    # sparces the sound from the spoken word
    data.value = (audio_compare(data.current_recording, os.getcwd() + 
        "/phonetic sounds/%s.wav" % data.phonetic_sounds[data.word_place]))

def add_word_to_dic(data):
    # adds the analysed frames to the dictionary of sounds
    data.sounds[data.phonetic_sounds[data.word_place]] = data.value

def get_sounds(word, data):
    # gets appropriate sounds to play
    results = []
    for sound in range(len(word)):
        if word[sound] in data.sounds:
            results.append(word[sound])
    return results

def turn_to_frames(data):
        # gets the appropriate sounds from the dictionary based on the typed

        #gets pronounciation from dictionary.com 
        pronouciation = phonetic_pronouciation(turn_to_string(data.word))
        
        # finds the list of words from the typed words
        words = turn_to_string3(data)
        results = []

        # if typed word is in the added words 
        for word in range(len(pronouciation)):
            sounds = get_sounds(pronouciation[word], data)
            start = 0
            if(words[word] in data.sounds and len(words[word]) > 1):
                for frame in range(len(data.sounds[words[word]])):
                    results.append(data.sounds[words[word]][frame])

            else:

                #adds the appropriate sounds from the dictionary 
                # combins the data.overlap % of the sounds
                for sound in range(len(sounds)):
                    try:
                        frames1 = remove_white_noise(data.sounds[sounds[sound]])
                        if(sound != len(sounds)-1):
                            frames2 = remove_white_noise(data.sounds[sounds[sound+1]])
                            splice = min(int(len(frames1) * data.overlap), int(len(frames2) * data.overlap))
                        else:
                            splice = 0 

                        for frame in range(start, len(frames1)-splice):
                            if(abs(audioop.avg(frames1[frame], 2)) > 8):
                                results.append(frames1[frame])

                        if(sound != len(sounds)-1):
                            for frame in range(splice):
                                if(len(frames1[len(frames1)-splice+frame]) != 0 and len(frames2[frame]) != 0
                                    and abs(audioop.avg(frames1[len(frames1)-splice+frame], 2)) > 8
                                    and abs(audioop.avg(frames2[frame], 2)) > 8):
                                    results.append(audioop.add(frames1[len(frames1)-splice+frame], frames2[frame], 2))
                    except:
                        pass
                    start = splice

        return results

def get_space(data):
    # gets a blank sound
    wf = wave.open(os.getcwd() + "/space.wav", 'rb')
    p = pyaudio.PyAudio()
    results = wf.readframes(data.chunk)
    p.terminate()
    return results

def update_saved(data):
    # updates the list of saved files from the directory of saved files
    data.saved = []
    possible = os.listdir(os.getcwd() + "/saved files")
    for saved_file in range(len(possible)):
        # removes the os file not relevant to the search
        if possible[saved_file] != ".DS_Store":
            data.saved.append(possible[saved_file])

def write(a, name):
    #saves information in the form of a string
    string = str(a)
    with open(os.getcwd() + name, "wt") as f:
        f.write(string[:-1])

def open_file(path, data):
    data.sounds = []
    def readFile(path):
        #gets string from saved file
        with open(os.getcwd() + path, "rt") as f:
            return f.read()
    # turns the saved file into a dictionary
    data.sounds = ast.literal_eval(readFile(path) + "}")

def draw_traingle(canvas, data, centerx, centery, flip):
    # draws an equilateral triangle of a designated radius 
    # by changing the radius from positive to negative it flips the triangle
    radius = flip * data.radius
    angle = math.radians(60)
    points = [centerx, centery - radius, centerx - math.sin(angle) * radius, centery + radius * math.cos(angle), centerx + radius * math.sin(angle), centery + radius * math.cos(angle)]
    canvas.create_polygon(points, fill='grey', outline = "black", width=2)

####################################
# customize these functions
####################################

def init(data):
    # list of phonetic based words with the capitilized parts that you should 
    # emphasise and list of corresponding phonetic sounds
    data.phonetic_words = ["Up", "fAther", "At", "mEt", "Away", "tURn", "It", "sEE", 
    "Ought", "cAll", "pUt", "blUE", "EYE", "nOW", "EIGHt", "OH", "bOY", "AIR", 
    "Ear", "pURE", "Bee", "Did", "Find", "Give", "How", "Yes", "Cat", "Leg", 
    "Man", "No", "siNG", "Pet", "Red", "Sun", "SHe", "eaT", "CHeck", 
    "THink", "THis", "Voice", "Wet", "Zoo", "Sure", "Just"]
    data.phonetic_sounds = ["ʌ", "ɑ", "æ", "ɛ", "ə", "ɜ", "ɪ", "i", "ɒ", "ɔ", 
    "ʊ", "u", "aɪ", "aʊ", "eɪ", "oʊ", "ɔɪ", 'ɛə', "ɪə", "ʊə", "b", "d", "f", "g", 
    "h", "j", "k", "l", "m", "n", "ŋ", "p", "r", "s", "ʃ", "t", "tʃ", "θ", "ð", 
    "v", "w", "z", "ʒ", "dʒ"]

    data.word_place = -1
    data.format = pyaudio.paInt16
    data.channels = 2
    data.rate = 44100
    data.chunk = 1024//4

    data.current_recording = []
    data.sounds = dict()
    data.mode = "SplashScreen"
    data.word = []

    data.saved = []
    data.hold = []

    data.select = (-1,-1)
    data.saved_name = None
    data.values = ['comma', 'period', 'question', 'slash', 'quotedbl', 'quoteright', 'colon', 'semicolon', 'underscore', 'minus', 'parenright', 'parenleft']
    data.values2 = [',', '.', '?', '/', '"', "'", ':', ';', '_', '-', ')', '(']

    data.overlap = .7
    data.radius = 25

    data.value = []

def mousePressed(event, data):
    # use event.x and event.y
    def SplashScreen(event, data):
        # splash screen 

        if(event.x <= data.width//2-20 and event.y >= data.height//2 and  
            event.x >= data.width//2-240 and event.y <= data.height//2+50):
            # changes mode to train
            data.mode = "Train"
        if(event.x >= data.width//2+20 and event.y >= data.height//2 and 
            event.x <= data.width//2+240 and event.y <=data.height//2+50):
            # changes data mode to saved
            data.mode = "Saved"

    def Train(event, data):
        # training screen

        if(event.x >= data.width//2-110 and event.y <= data.height-20 and  
            event.x <= data.width//2+110 and event.y >= data.height - 80 and 
            data.word_place != -1):
            # rerecord
            new_sound(data)
            evaluate(data)
        
        if(event.x >= data.width//2-360 and event.y <= data.height-20 and 
            event.x <= data.width//2-140 and event.y >= data.height - 80 and 
            data.word_place != -1):
            # play
            data.current_recording = data.value
            play_sound(data)
        
        if(event.x >= data.width//2+140 and event.y <= data.height-20 and 
            event.x <= data.width//2+360 and event.y >= data.height - 80):
            # next word
            if(data.word_place != -1):
                add_word_to_dic(data)
                data.current_recording = []
                data.word_place += 1
                # once finished goes back to the splash screen
                if(data.word_place >= len(data.phonetic_words)):
                    data.mode = "SaveScreen"
            else:
                data.current_recording = []
                data.word_place += 1

    def SaveScreen(event, data):
        pass
        
    def Speak(event, data):
        # speaking screen

        if((event.x - 50)**2 + (event.y - (data.height//2 - 25))**2)*.5 <= data.radius * 2 * 3.14:
            data.rate += 1000
            # speed up
        elif((event.x - 50)**2 + (event.y - (data.height//2 + 25))**2)*.5 <= data.radius * 2 * 3.14 and data.rate > 999:
            data.rate -= 1000
            # speed down
        elif((event.x - (data.width - 50))**2 + (event.y - (data.height//2 - 25))**2)*.5 <= data.radius * 2 * 3.14:
            data.overlap += .05
            # overlap up
        elif((event.x - (data.width - 50))**2 + (event.y - (data.height//2 + 25))**2)*.5 <= data.radius * 2 * 3.14 and data.overlap > .04:
            data.overlap -= .05
            # overlap down

        if(event.x >= data.width//2-110 and event.y <= data.height-20 and  
            event.x <= data.width//2+110 and event.y >= data.height - 80):
            # reset
            data.word = []
            data.overlap = .7
            data.rate = 44100
        
        if(event.x >= data.width//2-360 and event.y <= data.height-20 and 
            event.x <= data.width//2-140 and event.y >= data.height - 70):
            # save
            save(turn_to_frames(data), os.getcwd() + "/saved sounds/" + 
                turn_to_string(data.word) + ".wav")

        if(event.x >= data.width//2+140 and event.y <= data.height-20 and 
            event.x <= data.width//2+360 and event.y >= data.height - 80):
            # play
            make_sound(data)

    def Saved(event, data):
        # saved file screen 

        # selects one of the files
        if(data.select != (-1,-1)):
            count = 0
            row, col = data.select

            for i in range(row + 1):
                if i == row:
                    go = col + 1
                else:
                    go = 3
                for j in range(go):
                    count += 1

            if(count > 0 and count <= len(data.saved)):
                if(event.x >= data.width//2-110 and event.y <= data.height-20 and  
                    event.x <= data.width//2+110 and event.y >= data.height - 80):
                    # changes to add screen
                    data.mode = "add"
                    data.select = (-1,-1)
                    data.word = []
                    data.saved_name = "/saved files/" + data.saved[count - 1]
                    open_file("/saved files/" + data.saved[count - 1], data)

                if(event.x >= data.width//2-360 and event.y <= data.height-20 and 
                    event.x <= data.width//2-140 and event.y >= data.height - 70):
                    # edit
                    os.remove(os.getcwd() + "/saved files/" + data.saved[count - 1])
                    data.select = (-1,-1)

                if(event.x >= data.width//2+140 and event.y <= data.height-20 and 
                    event.x <= data.width//2+360 and event.y >= data.height - 80):
                    # use
                    open_file("/saved files/" + data.saved[count - 1], data)
                    data.mode = "Speak"
                    data.select = (-1,-1)

        # opens one of the saved files
        col = -1
        row = -1
        if(event.x >= data.width//2-360 and event.x <= data.width//2-140):
            col = 0
        elif(event.x >= data.width//2-110 and event.x <= data.width//2+110):
            col = 1
        elif(event.x >= data.width//2+140 and event.x <= data.width//2+360):
            col = 2
        if col != -1:
            maxrow = math.ceil(len(data.saved)/3)
            for row_hold in range(maxrow):
                if(event.y >= 80 + 80 * row_hold and event.y <= 130 + 80 * row_hold):
                    row = row_hold
                    break
            count = 0
            for i in range(row + 1):
                if i == row:
                    go = col + 1
                else:
                    go = 3
                for j in range(go):
                    count += 1
            if(count > 0 and count <= len(data.saved)):
                data.select = (row, col)
        
    def Add(event, data):
        # add word screen 

        if(event.x >= data.width//2-110 and event.y <= data.height-20 and  
            event.x <= data.width//2+110 and event.y >= data.height - 80):
            new_sound(data)
            # hear
            pass

        if(event.x >= data.width//2-360 and event.y <= data.height-20 and 
            event.x <= data.width//2-140 and event.y >= data.height - 70):
            # re record
            play_sound(data)
            pass

        if(event.x >= data.width//2+140 and event.y <= data.height-20 and 
            event.x <= data.width//2+360 and event.y >= data.height - 80):
            if(not turn_to_string(data.word) in data.sounds):
                # done
                data.sounds[turn_to_string(data.word)] = remove_white_noise(data.current_recording)
                write(data.sounds, data.saved_name)
                data.mode = "Saved"
                data.word = []

            # done
            pass

    if(data.mode == "SplashScreen"):
        SplashScreen(event, data)
    if(data.mode == "Train"):
        Train(event, data)
    if(data.mode == "Speak"):
        Speak(event, data)
    if(data.mode == "Saved"):
        Saved(event, data)
    if(data.mode == "SaveScreen"):
        SaveScreen(event, data)
    if(data.mode == "add"):
        Add(event, data)
    pass

def keyPressed(event, data):
    # resets the system
    if(event.keysym == "1"):
        init(data)
    
    def SplashScreen(event, data):
        pass

    def Train(event, data):
        # creates new sound
        if(event.keysym == "space"):
            new_sound(data)

    def Speak(event, data):
        # creates the typed word on screen
        if((event.keysym.isalpha() and len(event.keysym) == 1) or event.keysym in data.values):
            if(event.keysym not in data.values): 
                data.word += [event.keysym]
            else: 
                data.word.append(data.values2[data.values.index(event.keysym)]) 
        elif(event.keysym == "space"):
            data.word += [" "]
        elif(event.keysym == "BackSpace" and len(data.word)>0):
            data.word.pop()
        elif(event.keysym == "Return"):
            make_sound(data)
        pass

    def SaveScreen(event, data):
        # creates typed word on screen
        if(event.keysym.isalpha() and len(event.keysym) == 1):
            data.word += [event.keysym]
        elif(event.keysym == "space"):
            data.word += [" "]
        elif(event.keysym == "BackSpace" and len(data.word)>0):
            data.word.pop()
        elif(event.keysym == "Return"):
            write(data.sounds, "/saved files/" + turn_to_string(data.word) + ".text")
            data.word = []
            data.mode = "SplashScreen"

    def Saved(event, data):
        pass

    def Add(event, data):
        # adds words not in the dictionary to the saved file
        if(event.keysym.isalpha() and len(event.keysym) == 1):
            data.word += [event.keysym]
        elif(event.keysym == "space"):
            data.word += [" "]
        elif(event.keysym == "BackSpace" and len(data.word)>0):
            data.word.pop()
        elif(event.keysym == "Return"):
            pass

    if(data.mode == "SplashScreen"):
        SplashScreen(event, data)
    if(data.mode == "Train"):
        Train(event, data)
    if(data.mode == "Speak"):
        Speak(event, data)
    if(data.mode == "Saved"):
        Saved(event, data)
    if(data.mode == "SaveScreen"):
        SaveScreen(event, data)
    if(data.mode == "add"):
        Add(event, data)
    pass
  
def timerFired(data):
    pass

def redrawAll(canvas, data):
    # background
    canvas.create_rectangle(0, 0, data.width, data.height, fill = "light blue")

    def SplashScreen(canvas, data):
        # title
        canvas.create_text(data.width//2, data.height//2-80,
                       text= "Text to Speech", font="Times 52 bold")

        # create new button
        canvas.create_rectangle(data.width//2-20, data.height//2, 
                        data.width//2-240, data.height//2+50, width = 3, fill = "grey")
        canvas.create_text((data.width//2-20 + data.width//2-240)//2, 
                        (data.height//2 + data.height//2+50)//2,
                        text="Create New", font="Times 24 bold", fill = "grey10")
        
        # use exhisting button
        canvas.create_rectangle(data.width//2+20, data.height//2, 
                        data.width//2+240, data.height//2+50, width = 3, fill = "grey")
        canvas.create_text((data.width//2+20 + data.width//2+240)//2, 
                        (data.height//2 + data.height//2+50)//2,
                        text="Use Existing", font="Times 24 bold", fill = "grey10")

    def Train(canvas, data):
        

        # spoken word
        if(data.word_place == -1):
            string = "Read the word on the screen emphasizing the capitalized part \n click the 'Hear Selection' key to hear if the process worked"
            canvas.create_text(data.width//2, data.height//2, text=string, 
                        font="Times 26 bold")
        else:
            canvas.create_text(data.width//2, data.height//2, text=data.phonetic_words[data.word_place], 
                        font="Times 64 bold", fill = "red")
            # title
            canvas.create_text(data.width//2, 40, 
                        text="Press record and read the word on the screen", 
                        font="Times 30 bold", fill = "grey10")
        
        if(data.word_place != -1):
            # record button
            canvas.create_rectangle(data.width//2-110, data.height-20, 
                            data.width//2+110, data.height - 70, width=3, fill = "grey")
            canvas.create_text((data.width//2-110 + data.width//2+110)//2, 
                            (data.height-20 + data.height-70)//2,
                            text="Record", font="Times 24 bold", fill = "grey10")
            
            # hear recording button
            canvas.create_rectangle(data.width//2-360, data.height-20, 
                            data.width//2-140, data.height - 70, width = 3, fill = "grey")
            canvas.create_text((data.width//2-360 + data.width//2-140)//2, 
                            (data.height-20 + data.height-70)//2,
                            text="Hear Selection", font="Times 24 bold", fill = "grey10")
            
        # next word button
        canvas.create_rectangle(data.width//2+140, data.height-20, 
                        data.width//2+360, data.height - 70, width = 3, fill = "grey")
        canvas.create_text((data.width//2+140 + data.width//2+360)//2, 
                        (data.height-20 + data.height-70)//2,
                        text="Next Word", font="Times 24 bold", fill = "grey10") 

    def Speak(canvas, data):
        # title
        canvas.create_text(data.width//2, 40, 
                        text="What would you like to hear pronounced?", 
                        font="Times 30 bold", fill = "grey10")

        # speed buttons
        canvas.create_text(50, data.height//2 - 70, 
                        text="SPEED", 
                        font="Times 15 bold", fill = "grey10")
        canvas.create_text(50, data.height//2 + 70, 
                        text=str(round(data.rate)), 
                        font="Times 15 bold", fill = "grey10")
        draw_traingle(canvas, data, 50, data.height//2 - 25, 1)
        draw_traingle(canvas, data, 50, data.height//2 + 25, -1)

        # overlap button
        canvas.create_text(data.width - 50, data.height//2 - 70, 
                        text="OVERLAP", 
                        font="Times 15 bold", fill = "grey10")
        canvas.create_text(data.width - 50, data.height//2 + 70, 
                        text=str(round(data.overlap * 100)) + ".0 %", 
                        font="Times 15 bold", fill = "grey10")
        draw_traingle(canvas, data, data.width - 50, data.height//2 - 25, 1)
        draw_traingle(canvas, data, data.width - 50, data.height//2 + 25, -1)

        # reset button
        canvas.create_rectangle(data.width//2-110, data.height-20, 
                        data.width//2+110, data.height - 70, width=3, fill = "grey")
        canvas.create_text((data.width//2-110 + data.width//2+110)//2, 
                        (data.height-20 + data.height-70)//2,
                        text="Reset", font="Times 24 bold", fill = "grey10")

        # save button
        canvas.create_rectangle(data.width//2-360, data.height-20, 
                        data.width//2-140, data.height - 70, width = 3, fill = "grey")
        canvas.create_text((data.width//2-360 + data.width//2-140)//2, 
                        (data.height-20 + data.height-70)//2,
                        text="Save", font="Times 24 bold", fill = "grey10")

        # lets hear button
        canvas.create_rectangle(data.width//2+140, data.height-20, 
                        data.width//2+360, data.height - 70, width = 3, fill = "grey")
        canvas.create_text((data.width//2+140 + data.width//2+360)//2, 
                        (data.height-20 + data.height-70)//2,
                        text="Lets Hear It!", font="Times 24 bold", fill = "grey10") 
        
        # typed words formated to be centered at the center of the screen
        # on line is <= 45 letters
        def create_start_list(number):
            if(number == 0): return [0]
            result = []
            start = 0
            if(number % 2 == 1):
                for i in range((-1 * int(number//2)), number//2+1):
                    result.append(i)
                return sorted(result)
            else:
                result = create_start_list(number-1)
                for i in range(len(result)):
                    result[i] = result[i] - .5
                return result + [-1 * result[0]]


        string = turn_to_string2(data)
        start_list = create_start_list(len(string))
        for word in range(len(string)):
            canvas.create_text(data.width//2, data.height//2 + 25 * start_list[word],
                       text=string[word], font="Times 26 bold")

    def Saved(canvas, data):
        # edit button
        canvas.create_rectangle(data.width//2-110, data.height-20, 
                        data.width//2+110, data.height - 70, width=3, fill = "grey")
        canvas.create_text((data.width//2-110 + data.width//2+110)//2, 
                        (data.height-20 + data.height-70)//2,
                        text="Edit", font="Times 24 bold", fill = "grey10")

        # delete button
        canvas.create_rectangle(data.width//2-360, data.height-20, 
                        data.width//2-140, data.height - 70, width = 3, fill = "grey")
        canvas.create_text((data.width//2-360 + data.width//2-140)//2, 
                        (data.height-20 + data.height-70)//2,
                        text="Delete", font="Times 24 bold", fill = "grey10")

        # use button
        canvas.create_rectangle(data.width//2+140, data.height-20, 
                        data.width//2+360, data.height - 70, width = 3, fill = "grey")
        canvas.create_text((data.width//2+140 + data.width//2+360)//2, 
                        (data.height-20 + data.height-70)//2,
                        text="Use", font="Times 24 bold", fill = "grey10") 

        # creats buttons for all saved files
        update_saved(data)
        count = 0
        for row in range(math.ceil(len(data.saved)/3)):
            for col in range(3):
                if(count == len(data.saved)):
                    break
                row_select, col_select = data.select
                if(row == row_select and col == col_select):
                    fill = "blue"
                else:
                    fill = "grey"

                if(col % 3 == 0):
                    canvas.create_rectangle(data.width//2-360, 80 + 80 * row, 
                            data.width//2-140, 130 + 80 * row, width = 3, fill = fill)
                    canvas.create_text((data.width//2-360 + data.width//2-140)//2, 
                        (80 + 80 * row + 130 + 80 * row)//2,
                        text=data.saved[count][:-5], font="Times 24 bold", fill = "grey10")

                if(col % 3 == 1):
                    canvas.create_rectangle(data.width//2-110, 80 + 80 * row, 
                        data.width//2+110, 130 + 80 * row, width=3, fill = fill)
                    canvas.create_text((data.width//2-110 + data.width//2+110)//2, 
                        (80 + 80 * row + 130 + 80 * row)//2,
                        text=data.saved[count][:-5], font="Times 24 bold", fill = "grey10")

                if(col % 3 == 2):
                    canvas.create_rectangle(data.width//2+140, 80 + 80 * row, 
                            data.width//2+360, 130 + 80 * row, width = 3, fill = fill)
                    canvas.create_text((data.width//2+140 + data.width//2+360)//2, 
                        (80 + 80 * row + 130 + 80 * row)//2,
                        text=data.saved[count][:-5], font="Times 24 bold", fill = "grey10")

                count += 1

        # title
        canvas.create_text(data.width//2, 40, 
                        text="What voice would you like to hear?", 
                        font="Times 30 bold")

    def SaveScreen(canvas, data):
        # title
        canvas.create_text(data.width//2, 40, 
                        text="What would you like to save as?", 
                        font="Times 30")

        # creates tyoed word on the middle of the screen
        string = turn_to_string(data.word)
        canvas.create_text(data.width//2, data.height//2,
                       text=string, font="Times 26 bold")

    def Add(canvas, data):
        # adds word to dictionary
        # words on screen 
        string = turn_to_string(data.word)
        canvas.create_text(data.width//2, data.height//2,
                       text=string, font="Times 26 bold")

        # title
        canvas.create_text(data.width//2, 40, 
                        text="What word would you like to add?", 
                        font="Times 30 bold", fill = "grey10")

        # record button
        canvas.create_rectangle(data.width//2-110, data.height-20, 
                        data.width//2+110, data.height - 70, width=3, fill = "grey")
        canvas.create_text((data.width//2-110 + data.width//2+110)//2, 
                        (data.height-20 + data.height-70)//2,
                        text="Record", font="Times 24 bold", fill = "grey10")

        # hear recording button
        canvas.create_rectangle(data.width//2-360, data.height-20, 
                        data.width//2-140, data.height - 70, width = 3, fill = "grey")
        canvas.create_text((data.width//2-360 + data.width//2-140)//2, 
                        (data.height-20 + data.height-70)//2,
                        text="Hear Recording", font="Times 24 bold", fill = "grey10")

        # done button
        canvas.create_rectangle(data.width//2+140, data.height-20, 
                        data.width//2+360, data.height - 70, width = 3, fill = "grey")
        canvas.create_text((data.width//2+140 + data.width//2+360)//2, 
                        (data.height-20 + data.height-70)//2,
                        text="Done", font="Times 24 bold", fill = "grey10") 


    if(data.mode == "SplashScreen"):
        SplashScreen(canvas, data)
    if(data.mode == "Train"):
        Train(canvas, data)
    if(data.mode == "Speak"):
        Speak(canvas, data)
    if(data.mode == "Saved"):
        Saved(canvas, data)
    if(data.mode == "SaveScreen"):
        SaveScreen(canvas, data)
    if(data.mode == "add"):
        Add(canvas, data)   
    pass

####################################
# use the run function as-is
####################################

def run(width=300, height=300):
    def redrawAllWrapper(canvas, data):
        canvas.delete(ALL)
        redrawAll(canvas, data)
        canvas.update()    

    def mousePressedWrapper(event, canvas, data):
        mousePressed(event, data)
        redrawAllWrapper(canvas, data)

    def keyPressedWrapper(event, canvas, data):
        keyPressed(event, data)
        redrawAllWrapper(canvas, data)

    def timerFiredWrapper(canvas, data):
        timerFired(data)
        redrawAllWrapper(canvas, data)
        # pause, then call timerFired again
        canvas.after(data.timerDelay, timerFiredWrapper, canvas, data)
    # Set up data and call init
    class Struct(object): pass
    data = Struct()
    data.width = width
    data.height = height
    data.timerDelay = 100 # milliseconds
    init(data)
    # create the root and the canvas
    root = Tk()
    canvas = Canvas(root, width=data.width, height=data.height)
    canvas.pack()
    # set up events
    root.bind("<Button-1>", lambda event:
                            mousePressedWrapper(event, canvas, data))
    root.bind("<Key>", lambda event:
                            keyPressedWrapper(event, canvas, data))
    timerFiredWrapper(canvas, data)
    # and launch the app
    root.mainloop()  # blocks until window is closed
    print("bye!")

run(800, 600)

