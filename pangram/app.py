import boto3
import uuid
import sys
import json
from botocore.exceptions import ClientError

dynamodb = boto3.client('dynamodb')
table_name = "pangram-data"

def pangram(input) :
    key = ''.join(sorted(dict.fromkeys(input.lower().replace(" ", ""))))
    response = dynamodb.get_item(TableName=table_name,
                                 Key={'id':{'S':key}})
    if 'Item' in response:
        return response['Item'].get('words').get('SS')
    else:
        return []
    
def lambda_handler(event, context) :
    headers = {
            "Access-Control-Allow-Headers": 
            "Content-Type,Authorization,X-Amz-Date,X-Api-Key,X-Amz-Security-Token",
            "Access-Control-Allow-Methods": "GET",
            "Access-Control-Allow-Origin": "http://dict.rkocherl.net"
        };
    try :
        matches = pangram(event['queryStringParameters']['pattern'])

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
        

