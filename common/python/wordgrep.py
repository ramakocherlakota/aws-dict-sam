import os

# the full word list, shipped in this layer alongside this module
WORDS_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "words.txt")

def read_words(filename=WORDS_FILE):
    with open(filename) as file:
        for line in file:
            yield line.rstrip()

def grep_file(regex, filename):
    matches = []
    for word in read_words(filename):
        if regex.fullmatch(word):
            matches.append(word)
    return matches
