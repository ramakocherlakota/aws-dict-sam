import json
import re
from sys import argv
from wordgrep import grep_file

def regex_match(pattern) :
    regex = re.compile(pattern, re.IGNORECASE)
    return grep_file(regex, "words.txt")

def lambda_handler(event, context) :
    headers = {
        "Access-Control-Allow-Headers":
        "Content-Type,Authorization,X-Amz-Date,X-Api-Key,X-Amz-Security-Token",
        "Access-Control-Allow-Methods": "GET",
        "Access-Control-Allow-Origin": "http://dict.rkocherl.net"
    };
    input = event['queryStringParameters']['pattern']
    print("pattern=" + input)
    try :
        matches = regex_match(input)
    except re.error as err :
        return {
            "headers": headers,
            "statusCode": 400,
            "body": json.dumps(
                {"error": {"message": "Invalid regular expression: " + str(err)}}
            )
        }
    return {
        "headers" : headers,
        "statusCode": 200,
        "body": json.dumps(
            {"matches": matches}
        )
    }


if __name__ == "__main__":
    print(regex_match(argv[1]))
