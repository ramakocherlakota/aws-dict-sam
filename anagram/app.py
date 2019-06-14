import boto3
import uuid
import sys
import json
from botocore.exceptions import ClientError

dynamodb = boto3.client('dynamodb')
table_name = "anagram-data"

def anagram(input) :
    key = ''.join(sorted(input.lower().replace(" ", "")))
    response = dynamodb.get_item(TableName=table_name,
                                 Key={'id':{'S':key}})
    if 'Item' in response:
        return response['Item'].get('words').get('SS')
    else:
        return []
    
def lambda_handler(event, context) :
    try :
        matches = anagram(event['queryStringParameters']['pattern'])
        headers = {
                "Access-Control-Allow-Headers": 
                "Content-Type,Authorization,X-Amz-Date,X-Api-Key,X-Amz-Security-Token",
                "Access-Control-Allow-Methods": "GET",
                "Access-Control-Allow-Origin": "https://dict.ramakocherlakota.net"
            };
        return {
            "headers": headers,
            "statusCode": 200,
            "body": json.dumps(
                {"matches": matches}
            )
        }
    except ClientError as err :
        return {
            "headers": headers,
            "statusCode": 500,
            "body": json.dumps(
                {
                    "error": {
                        "code" : err.response['Error']['Code'],
                        "message" : err.response['Error']['Message']
                    }
                }
            )
        }
        

