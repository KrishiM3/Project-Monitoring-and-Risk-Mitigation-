import boto3
import simplejson as json
from boto3.dynamodb.conditions import Key, Attr
from botocore.exceptions import ClientError
from boto3.dynamodb.types import TypeDeserializer

dynamodb = boto3.client('dynamodb')
table_name = 'Project'

def lambda_handler(event, context):
    try:
        event = json.loads(event['body'])
        
        project_name = event.get('project_name')
        status = event.get('status')
        description = event.get('description')
        email = event.get('email')
        deadline = event.get('deadline')
        risk_eval = event.get('risk_eval')
        project_id = event.get('project_id')
        team = event.get('team')
        start_date = event.get('start_date')
        
        # byte_id = (f"{project_name}{email}").encode('utf-8')
        # project_id = (bcrypt.hashpw(byte_id, salt)).decode('utf-8')
        
        dynamodb.put_item(
            TableName=table_name,
            Item={
                'project_id': {'S': project_id},
                'status': {'N': str(status)},
                'deadline': {'S': deadline},
                'project_name': {'S': project_name},
                'risk_eval': {'N': str(risk_eval)},
                'email': {'S': email},
                'description': {'S': description},
                'team': {'L': [{'S': x} for x in team] },
                'start_date': {'S': start_date}
            }
        )
        
        return {"code": 200, "message": "Project added successfully"}
    except dynamodb.exceptions.ConditionalCheckFailedException:
        return {"code": 400, "message": f"Project with same name already exists"}
    except Exception as e:
        return {"code": 500, "message": f"An unexpected error occurred while adding project: {e}"}