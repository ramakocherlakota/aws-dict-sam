import json
import re
from sys import argv
from wordgrep import read_words

def pangram(input) :
    # words that use every one of the given letters and no others
    letters = set(re.sub("[^a-z]", "", input.lower()))
    if not letters :
        return []
    return [word for word in read_words() if set(word) == letters]

def lambda_handler(event, context) :
    headers = {
        "Access-Control-Allow-Headers":
        "Content-Type,Authorization,X-Amz-Date,X-Api-Key,X-Amz-Security-Token",
        "Access-Control-Allow-Methods": "GET",
        "Access-Control-Allow-Origin": "http://dict.rkocherl.net"
    };
    input = event['queryStringParameters']['pattern']
    print("pattern=" + input)
    matches = pangram(input)
    return {
        "headers" : headers,
        "statusCode": 200,
        "body": json.dumps(
            {"matches": matches}
        )
    }


if __name__ == "__main__":
    print(pangram(argv[1]))
