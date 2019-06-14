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
    

