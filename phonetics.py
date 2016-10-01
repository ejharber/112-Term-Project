import requests
import string

def phonetic_word_simple(string):
    # finds the simple phonetic pronounciation
    string = string.lower()
    if(string == "the"): return "th ee"
    r = requests.get("http://dictionary.reference.com/browse/%s?s=t" % (string))
    x = r.text
    start = 0
    end = 0
    for i in range(len(x)):
        if(x[i:i+9] == "spellpron"):
            start = i+12
        elif(start != 0 and (x[i] == "," or x[i] == "]")):
            end = i
            break
    return remove_extraneous(x[start:end])

def remove_extraneous(code):
    # removes the extraneous parts of the code 
    mess = ""
    look = "offf" 
    count = 0
    add = True
    for i in range(len(code)):
        #looks for the end of each comment
        #if not in a comment adds to mess
        if(code[count:count+1] == look or code[count:count+3] == look):
            look = "offf"
            add = True
            count += 1
        elif(code[count:count+1] == "<" and look == "offf"):
            look = ">"
            add = False
        elif(code[count:count+1] == ";" and look == "offf"): break
        if(add): mess += code[count:count+1]
        count +=1 
    return mess

def phonetic_word_simple(string):
    # finds simplified verson from dictionary.com
    string = string.lower()
    if(string == "the"): return "th ee"
    r = requests.get("http://dictionary.reference.com/browse/%s?s=t" % (string))
    x = r.text
    start = 0
    end = 0
    for i in range(len(x)):
        if(x[i:i+9] == "spellpron"):
            start = i+12
        elif(start != 0 and (x[i] == "," or x[i] == "]")):
            end = i
            break
    return remove_extraneous(x[start:end])

def phonetic_word_complex(string, start = 0):
    # finds the phonetic spelling from the html code for dictionary.com
    string = string.lower()
    #if(string == "the"): return "th ee"
    r = requests.get("http://dictionary.reference.com/browse/%s?s=t" % (string))
    x = r.text
    end = start
    for i in range(len(x)):
        if(x[i:i+12] == "pron ipapron"):
            start = i+15
        elif(start != 0 and i-start > 1 and (x[i] == "<" or x[i] == "]" or x[i] == ",")):
            end = i
            break 

    return remove_surrounding(x[start:end])

def remove_surrounding(string):
    # removes non alphabetical section of the phoetic stuff
    results = []
    for part in range(len(string)):
        if(string[part].isalpha()):
            results.append(string[part])
    return results

def remove_puncuation(string):
    # removes the puncuation from the given string
    for i in range(len(string)):
        if(not string[i].isalpha()):
            string = string[:i] + " "  + string[i+1:]
    return string

duplicate = ['aɪ', 'aʊ', 'eɪ', 'oʊ', 'ɔɪ', 'ɛə', 'ɪə', 'ʊə', 'tʃ', 'dʒ']

def consolidate(phonetic):
    # removes the extraneous sections of the word list
    for word in range(len(phonetic)):
        results = []
        skip = False
        for sound in range(len(phonetic[word])):
            if(skip):
                skip = False
                continue
            if(sound != len(phonetic[word]) - 1):
                string = phonetic[word][sound] + phonetic[word][sound + 1]
                if(string in duplicate):
                    results.append(string)
                    skip = True
                else: results.append(phonetic[word][sound ])
            else:
                results.append(phonetic[word][sound ])

        phonetic[word] = results
    return phonetic

def phonetic_pronouciation(words):
    # finds the phonetic pronounciation from dictionary.com
    words = remove_puncuation(words)
    words = words.split()
    phonetic = []
    for i in words:
    # iterates through the sentence and finds the phonetic spelling of each word
        if(i == "the"):
            phonetic += [["ð","i"]]
        if(i == "mouth"):
            phonetic += [["m", "aʊ" , "ð"]]
        else:
            hold = phonetic_word_complex(i)
            try:
                # adds the "s" to the end 
                if(i[-1] == "s" and hold[-1] != "s"):
                    hold.append("s")
                phonetic.append(hold)
            except:
                pass
    return consolidate(phonetic)

# print(phonetic_pronouciation("sounds"))

# a = ["Up", "Arm", "At", "Edward", "Away", "It", "See", 
#     "Otter", "Four", "Put", "Food", "Eye", "Out", "Eight", "Oh", "Boy", "Air", 
#     "Ear", "Urn", "Bad", "Did", "Find", "Give", "How", "Yes", "Cat", "Leg", 
#     "Man", "No", "Sing", "Pet", "Red", "Sun", "She", "Tea", "She", "Check", 
#     "Think", "This", "Voice", "Wet", "Zoo", "Sure", "Just"]



