import boto3
import simplejson as json
from boto3.dynamodb.conditions import Key, Attr
from botocore.exceptions import ClientError
from boto3.dynamodb.types import TypeDeserializer

dynamodb = boto3.client('dynamodb')
table_name = 'TeamMembers'

def lambda_handler(event, context):
    try:
        event = json.loads(event['body']);
        id = event.get('id');
        name = event.get('name');
        email = event.get('email');
        description = event.get('description');
        skill = event.get('skill');
        salary = event.get('salary');
        
        dynamodb.put_item(
            TableName=table_name,
            Item={
                'id': {'S': id},
                'name': {'S':name},
                'email': {'S':email},
                'description': {'S':description},
                'skill': {'N': str(skill)},
                'salary': {'N': str(salary)}
            }    
        );
    
        return {
            'statusCode': 200,
            'body': json.dumps('Successful')
        }
    except Exception as e:
        return {
            'statusCode': 200,
            'body': json.dumps(str(e))
        }
