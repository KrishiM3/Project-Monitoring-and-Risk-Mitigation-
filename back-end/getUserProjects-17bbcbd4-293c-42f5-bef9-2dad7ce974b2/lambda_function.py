import simplejson as json
import boto3
from boto3.dynamodb.conditions import Key, Attr
from botocore.exceptions import ClientError
from boto3.dynamodb.types import TypeDeserializer

dynamodb = boto3.resource('dynamodb')
def lambda_handler(event, context):
    try:
        body = json.loads(event['body'])
        project_table = dynamodb.Table('Project')
        response = project_table.scan(
            FilterExpression=Attr('email').eq(body['email'])
        )
        items = response['Items']
        
        return json.dumps({
            'statusCode': 200,
            'body': items
        })
    except Exception as e:
        print(e)
        return json.dumps({
            'statusCode': 400,
            'body': json.dumps(str(e))#'Retrieval Failed')
        })

