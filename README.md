# aws-dict-sam

Back end of dictionary program. Enter a string like "m.c.i.e" to get words that fit the pattern - like "machine". Or select Anagram to find anagrams of a set of letters, either as one word or split into several words of lengths you pick (e.g. "dormitory" as 2 words of 5 and 4 letters gives "dirty room"), Pangram to find pangrams, or Regex to match words against an arbitrary regular expression (e.g. "^re.*ing$"). Try it out at http://dict.rkocherl.net/index.html

All lookups run against the word list in common/python/words.txt, shared through a Lambda layer; there's no database.

Front end code is in my aws-dict repo
