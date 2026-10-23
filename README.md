# aws-dict-sam

Back end of dictionary program. Enter a string like "m.c.i.e" to get words that fit the pattern - like "machine". Or select Anagram to find anagrams of a set of letters, Multi-Anagram to split a set of letters into several words of given lengths (e.g. "dormitory" with lengths "5 4" gives "dirty room"), Pangram to find pangrams, or Regex to match words against an arbitrary regular expression (e.g. "^re.*ing$"). Try it out at https://dict.ramakocherlakota.net/index.html

All lookups run against the word list in common/python/words.txt, shared through a Lambda layer; there's no database.

Front end code is in my aws-dict repo
