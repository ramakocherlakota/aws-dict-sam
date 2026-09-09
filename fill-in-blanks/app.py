import json
import re
from sys import argv
from wordgrep import grep_file

def fill_in_blanks(input) :
    pattern = input.lower().replace(" ", ".").replace('\u2026', '...')
    lenPattern = len(pattern)
    regex = re.compile(pattern, re.IGNORECASE)
    return grep_file(regex, f"words_{lenPattern}.txt")

def lambda_handler(event, context) :
    input = event['queryStringParameters']['pattern']
    print("pattern=" + input)
    matches = fill_in_blanks(input)
    headers = {
        "Access-Control-Allow-Headers": 
        "Content-Type,Authorization,X-Amz-Date,X-Api-Key,X-Amz-Security-Token",
        "Access-Control-Allow-Methods": "GET",
        "Access-Control-Allow-Origin": "http://dict.rkocherl.net"
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
