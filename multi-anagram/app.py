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

def parse_words(input) :
    return [word for word in re.split("[^a-z]+", (input or "").lower()) if word]

def multi_anagram(input, lengths, deadline=None, offset=0, include=(), exclude=()) :
    """Find all ways to split the letters of input into words of the given
    lengths. With no lengths, finds single-word anagrams. Returns one page of
    up to MAX_RESULTS matches starting at offset, as (matches, more,
    timed_out): more says there are matches after this page, timed_out that
    the search stopped early. Each match is a string of words separated by
    spaces, in the order of lengths. Matches come in the order the search
    finds them, which is the same on every call, so pages line up.
    Words in include appear in every match; words in exclude in none."""
    if deadline is None :
        deadline = time.monotonic() + TIME_LIMIT_SECONDS
    letters = re.sub("[^a-z]", "", input.lower())
    if lengths is None :
        # single-word anagram: nothing to match for empty input or for more
        # letters than any word has, as with the old table lookup
        if not letters or len(letters) > MAX_LETTERS :
            return [], False, False
        lengths = [len(letters)]
    if not lengths or any(n < 1 for n in lengths) :
        raise ValueError("Word lengths must be positive numbers")
    if len(letters) > MAX_LETTERS :
        raise ValueError(f"At most {MAX_LETTERS} letters are allowed")
    if sum(lengths) != len(letters) :
        raise ValueError(f"Word lengths add up to {sum(lengths)} but there are {len(letters)} letters")

    pool = letter_counts(letters)
    words = words_by_length()

    # Words the caller says are definitely in the answer take their letters
    # and one slot of their length before the search starts
    slots_left = list(lengths)
    for word in include :
        if len(word) not in slots_left :
            raise ValueError(f"There's no word of length {len(word)} left for \"{word}\"")
        counts = letter_counts(word)
        if not fits(counts, pool) :
            raise ValueError(f"There aren't enough letters left for \"{word}\"")
        slots_left.remove(len(word))
        pool -= counts
    excluded = set(exclude)

    # For each needed length, group the words that can be made from the pool
    # by their sorted letters, so the search runs over letter sets rather
    # than individual words.
    candidates = {}
    for n in set(lengths) :
        groups = defaultdict(list)
        for word in words.get(n, []) :
            if word in excluded :
                continue
            counts = letter_counts(word)
            if fits(counts, pool) :
                groups[''.join(sorted(word))].append(word)
        candidates[n] = groups

    # Every letter has to be used, so at each step pick the remaining letter
    # that the fewest candidate words can cover and branch on the words that
    # cover it. This prunes far better than filling slots in a fixed order.
    # The search is a generator, so it only runs as far as the page asked for.
    # (remaining lengths, remaining letters) states known to lead nowhere
    dead_ends = set()
    timed_out = False

    def search(lengths_left, remaining, options, chosen) :
        # lengths_left is a sorted tuple of the word lengths still to fill and
        # options maps each of those lengths to the candidates that still fit.
        # Yields each solution as a sorted tuple of (length, key) pairs.
        nonlocal timed_out
        if not lengths_left :
            yield tuple(sorted(chosen))
            return
        state = (lengths_left, remaining)
        if state in dead_ends :
            return
        if time.monotonic() > deadline :
            timed_out = True
            return
        fitting = {}
        for n in set(lengths_left) :
            fitting[n] = [opt for opt in options[n] if fits(opt[1], remaining)]
            if not fitting[n] :
                dead_ends.add(state)
                return
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
                    return
                if best is None or coverage[i] < coverage[best] :
                    best = i
        found = False
        # sorted so the order doesn't depend on set iteration order
        for n in sorted(fitting) :
            rest = list(lengths_left)
            rest.remove(n)
            rest = tuple(rest)
            for key, counts, letters_in_key in fitting[n] :
                if best in letters_in_key :
                    chosen.append((n, key))
                    for solution in search(rest, remaining - counts, fitting, chosen) :
                        found = True
                        yield solution
                    chosen.pop()
                    if timed_out :
                        return
        if not found :
            dead_ends.add(state)

    # Turn each solution into word combinations in the caller's order of
    # lengths. Slots of equal length are interchangeable, so each set of
    # words is listed once rather than once per permutation.
    slots_by_length = defaultdict(list)
    for i, n in enumerate(lengths) :
        slots_by_length[n].append(i)

    def expand(solution) :
        per_length = []
        for n, slots in sorted(slots_by_length.items()) :
            keys = [key for length, key in solution if length == n]
            choices = [combinations_with_replacement(candidates[n][key], keys.count(key))
                       for key in sorted(set(keys))]
            per_length.append((slots, [sum(combo, ()) for combo in product(*choices)]))
        for combo in product(*(words for slots, words in per_length)) :
            result = [None] * len(lengths)
            for (slots, _), words in zip(per_length, combo) :
                for slot, word in zip(slots, words) :
                    result[slot] = word
            yield ' '.join(result)

    options = {n : [(key, letter_counts(key), frozenset(ord(c) - 97 for c in key))
                    for key in sorted(groups)]
               for n, groups in candidates.items()}
    # Included words join every solution as groups of their own; the "+"
    # can't clash with a real letter key
    fixed = []
    for word in include :
        candidates[len(word)]["+" + word] = [word]
        fixed.append((len(word), "+" + word))
    # A solution can be reached more than once when a letter is repeated
    seen = set()
    page = []
    index = 0
    more = False
    for solution in search(tuple(sorted(slots_left)), pool, options, []) :
        if solution in seen :
            continue
        seen.add(solution)
        solution = tuple(sorted(solution + tuple(fixed)))
        for match in expand(solution) :
            if index >= offset + MAX_RESULTS :
                more = True
                break
            if index >= offset :
                page.append(match)
            index += 1
        if more :
            break
    return sorted(page), more, timed_out

def lambda_handler(event, context) :
    headers = {
        "Access-Control-Allow-Headers":
        "Content-Type,Authorization,X-Amz-Date,X-Api-Key,X-Amz-Security-Token",
        "Access-Control-Allow-Methods": "GET",
        "Access-Control-Allow-Origin": "http://dict.rkocherl.net"
    };
    params = event['queryStringParameters'] or {}
    input = params.get('pattern', '')
    try :
        offset = max(0, int(params.get('offset') or 0))
    except ValueError :
        offset = 0
    # /anagram passes no lengths and gets single-word anagrams
    lengths = parse_lengths(params['lengths']) if params.get('lengths') else None
    # comma-separated words to require in, or rule out of, every match
    include = parse_words(params.get('include'))
    exclude = parse_words(params.get('exclude'))
    print("pattern=" + input + " lengths=" + str(lengths) + " include=" + str(include) + " exclude=" + str(exclude))
    # stop searching with a few seconds of the Lambda's time left, so a long
    # search still returns its partial results instead of being killed
    time_limit = TIME_LIMIT_SECONDS
    if context :
        time_limit = min(time_limit, context.get_remaining_time_in_millis() / 1000 - 5)
    deadline = time.monotonic() + time_limit
    try :
        matches, more, timed_out = multi_anagram(input, lengths, deadline, offset, include, exclude)
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
            {"matches": matches, "offset": offset, "more": more, "timed_out": timed_out,
             # kept for older pages: something was left out of this response
             "truncated": more or timed_out}
        )
    }


if __name__ == "__main__":
    print(multi_anagram(argv[1], parse_lengths(argv[2]) if len(argv) > 2 else None))
