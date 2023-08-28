import simplejson as json
import boto3
from boto3.dynamodb.conditions import Key, Attr
from botocore.exceptions import ClientError
from boto3.dynamodb.types import TypeDeserializer

dynamodb = boto3.resource('dynamodb')
def lambda_handler(event, context):
    try:
        event = json.loads(event['body'])
        project_table = dynamodb.Table('Project')
        response = project_table.get_item(
            Key={
               'project_id': event['id']
             }
        )
        item = response['Item']
        print(item)
        
        task_table = dynamodb.Table('To_Do_List')
        response = task_table.scan(
            FilterExpression=Attr('project_id').eq(event['id'])
        )
        tasks = response['Items']

        return json.dumps({
            'statusCode': 200,
            'body': {
                'project': item,
                'tasks': tasks
            }
        })
    except Exception as e:
        print(e)
        return json.dumps({
            'statusCode': 400,
            'body': json.dumps(str(e)) #'Retrieval Failed'
        })
