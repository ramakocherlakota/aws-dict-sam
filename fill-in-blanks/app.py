import json
import re
import requests

def fill_in_blanks(input) :
    matches = []
    pattern = input.lower().replace(" ", ".")
    lenPattern = len(pattern)
    regex = re.compile("^"+pattern+"$")
    with open(f"words_{lenPattern}.txt") as file :
        for line in file :
            word = line.rstrip()
            if regex.match(word) :
                matches.append(word)
    return matches

def lambda_handler(event, context) :
    matches = fill_in_blanks(event['queryStringParameters']['pattern'])
    return {
        "statusCode": 200,
        "body": json.dumps(
            {"matches": matches}
        )
    }
    

