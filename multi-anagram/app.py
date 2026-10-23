import json
import re
import time
from collections import defaultdict
from itertools import combinations_with_replacement, product
from sys import argv
from wordgrep import read_words

MAX_RESULTS = 1000
TIME_LIMIT_SECONDS = 20
MAX_LETTERS = 60

# Letter counts are packed into one integer, 8 bits per letter, so checking
# whether a word fits in the remaining letters is a single subtraction: the
# high bit of each field acts as a guard that is cleared when a count goes
# negative.
GUARD = sum(0x80 << (8 * i) for i in range(26))

_words_by_length = None

def letter_counts(s) :
    counts = 0
    for c in s :
        counts += 1 << (8 * (ord(c) - 97))
    return counts

def fits(counts, remaining) :
    return ((remaining | GUARD) - counts) & GUARD == GUARD

def words_by_length() :
    # loaded once per Lambda container and reused across warm invocations
    global _words_by_length
    if _words_by_length is None :
        _words_by_length = defaultdict(list)
        valid = re.compile("[a-z]+")
        for word in read_words() :
            if valid.fullmatch(word) :
                _words_by_length[len(word)].append(word)
    return _words_by_length

def parse_lengths(input) :
    return [int(n) for n in re.findall(r"\d+", input)]

def multi_anagram(input, lengths) :
    """Find all ways to split the letters of input into words of the given
    lengths. With no lengths, finds single-word anagrams. Returns
    (matches, truncated) where each match is a string of words separated by
    spaces, in the order of lengths."""
    letters = re.sub("[^a-z]", "", input.lower())
    if lengths is None :
        lengths = [len(letters)]
    if not lengths or any(n < 1 for n in lengths) :
        raise ValueError("Word lengths must be positive numbers")
    if len(letters) > MAX_LETTERS :
        raise ValueError(f"At most {MAX_LETTERS} letters are allowed")
    if sum(lengths) != len(letters) :
        raise ValueError(f"Word lengths add up to {sum(lengths)} but there are {len(letters)} letters")

    pool = letter_counts(letters)
    words = words_by_length()

    # For each needed length, group the words that can be made from the pool
    # by their sorted letters, so the search runs over letter sets rather
    # than individual words.
    candidates = {}
    for n in set(lengths) :
        groups = defaultdict(list)
        for word in words.get(n, []) :
            counts = letter_counts(word)
            if fits(counts, pool) :
                groups[''.join(sorted(word))].append(word)
        candidates[n] = groups

    # Every letter has to be used, so at each step pick the remaining letter
    # that the fewest candidate words can cover and branch on the words that
    # cover it. This prunes far better than filling slots in a fixed order.
    # A solution is a multiset of (length, key) pairs; it can be reached more
    # than once when a letter is repeated, so solutions are kept in a set.
    solutions = set()
    # (remaining lengths, remaining letters) states known to lead nowhere
    dead_ends = set()
    deadline = time.monotonic() + TIME_LIMIT_SECONDS
    timed_out = False

    def search(lengths_left, remaining, options, chosen) :
        # lengths_left is a sorted tuple of the word lengths still to fill and
        # options maps each of those lengths to the candidates that still fit.
        # Returns True if at least one solution was found from this state.
        nonlocal timed_out
        if not lengths_left :
            solutions.add(tuple(sorted(chosen)))
            return True
        state = (lengths_left, remaining)
        if state in dead_ends :
            return False
        if time.monotonic() > deadline :
            timed_out = True
            return False
        fitting = {}
        for n in set(lengths_left) :
            fitting[n] = [opt for opt in options[n] if fits(opt[1], remaining)]
            if not fitting[n] :
                dead_ends.add(state)
                return False
        coverage = defaultdict(int)
        for opts in fitting.values() :
            for opt in opts :
                for letter in opt[2] :
                    coverage[letter] += 1
        best = None
        for i in range(26) :
            if (remaining >> (8 * i)) & 0xff :
                if coverage[i] == 0 :
                    dead_ends.add(state)
                    return False
                if best is None or coverage[i] < coverage[best] :
                    best = i
        found = False
        for n, opts in fitting.items() :
            rest = list(lengths_left)
            rest.remove(n)
            rest = tuple(rest)
            for key, counts, letters_in_key in opts :
                if best in letters_in_key :
                    chosen.append((n, key))
                    if search(rest, remaining - counts, fitting, chosen) :
                        found = True
                    chosen.pop()
                    if timed_out or len(solutions) >= MAX_RESULTS :
                        return found
        if not found :
            dead_ends.add(state)
        return found

    options = {n : [(key, letter_counts(key), frozenset(ord(c) - 97 for c in key))
                    for key in groups]
               for n, groups in candidates.items()}
    search(tuple(sorted(lengths)), pool, options, [])

    # Turn each solution into word combinations in the caller's order of
    # lengths. Slots of equal length are interchangeable, so each set of
    # words is listed once rather than once per permutation.
    slots_by_length = defaultdict(list)
    for i, n in enumerate(lengths) :
        slots_by_length[n].append(i)
    matches = []
    truncated = timed_out
    for solution in sorted(solutions) :
        per_length = []
        for n, slots in slots_by_length.items() :
            keys = [key for length, key in solution if length == n]
            choices = [combinations_with_replacement(candidates[n][key], keys.count(key))
                       for key in sorted(set(keys))]
            per_length.append((slots, [sum(combo, ()) for combo in product(*choices)]))
        for combo in product(*(words for slots, words in per_length)) :
            result = [None] * len(lengths)
            for (slots, _), words in zip(per_length, combo) :
                for slot, word in zip(slots, words) :
                    result[slot] = word
            matches.append(' '.join(result))
            if len(matches) >= MAX_RESULTS :
                break
        if len(matches) >= MAX_RESULTS :
            truncated = True
            break
    if len(solutions) >= MAX_RESULTS :
        truncated = True
    return sorted(matches), truncated

def lambda_handler(event, context) :
    headers = {
        "Access-Control-Allow-Headers":
        "Content-Type,Authorization,X-Amz-Date,X-Api-Key,X-Amz-Security-Token",
        "Access-Control-Allow-Methods": "GET",
        "Access-Control-Allow-Origin": "http://dict.rkocherl.net"
    };
    params = event['queryStringParameters'] or {}
    input = params.get('pattern', '')
    # /anagram passes no lengths and gets single-word anagrams
    lengths = parse_lengths(params['lengths']) if params.get('lengths') else None
    print("pattern=" + input + " lengths=" + str(lengths))
    try :
        matches, truncated = multi_anagram(input, lengths)
    except ValueError as err :
        return {
            "headers": headers,
            "statusCode": 400,
            "body": json.dumps(
                {"error": {"message": str(err)}}
            )
        }
    return {
        "headers" : headers,
        "statusCode": 200,
        "body": json.dumps(
            {"matches": matches, "truncated": truncated}
        )
    }


if __name__ == "__main__":
    print(multi_anagram(argv[1], parse_lengths(argv[2]) if len(argv) > 2 else None))
