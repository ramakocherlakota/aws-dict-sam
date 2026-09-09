def grep_file(regex, filename):
    matches = []
    with open(filename) as file:
        for line in file:
            word = line.rstrip()
            if regex.fullmatch(word):
                matches.append(word)
    return matches
