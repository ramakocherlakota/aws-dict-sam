import json
import re
import requests
from sys import argv

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
    input = event['queryStringParameters']['pattern']
    print("pattern=" + input)
    matches = fill_in_blanks(input)
    headers = {
        "Access-Control-Allow-Headers": 
        "Content-Type,Authorization,X-Amz-Date,X-Api-Key,X-Amz-Security-Token",
        "Access-Control-Allow-Methods": "GET",
        "Access-Control-Allow-Origin": "https://dict.ramakocherlakota.net"
    };
    return {
        "headers" : headers,
        "statusCode": 200,
        "body": json.dumps(
            {"matches": matches}
        )
    }
    

if __name__ == "__main__":
    print(fill_in_blanks(argv[1]))
