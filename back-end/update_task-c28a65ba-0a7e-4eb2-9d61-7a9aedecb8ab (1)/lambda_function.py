import boto3
from boto3.dynamodb.conditions import Key, Attr
from botocore.exceptions import ClientError
from boto3.dynamodb.types import TypeDeserializer
import json

dynamodb = boto3.client('dynamodb')
table_name = 'To_Do_List'

def lambda_handler(event, context):
    try:
        event = json.loads(event['body'])

        t_id = event.get('id')
        project_id = event.get('project_id')
        complete = event.get('complete')
        deadline = event.get('deadline')
        date_added = event.get('date_added')
        priority = event.get('priority')
        task_desc = event.get('task_desc')
                
        dynamodb.put_item(
            TableName=table_name,
            Item={
                'id': {'S':t_id},
                'project_id': {'S':project_id},
                'complete': {'BOOL':complete},
                'deadline': {'S':deadline},
                'date_added': {'S':date_added},
                'priority': {'N':str(priority)},
                'task_desc': {'S':task_desc}
            }
        )
        
        return {"code": 200, "message": "Task added successfully"}
    except Exception as e:
        return {"code": 400, "message": f"An unexpected error occurred while adding task: {e}"}
        
