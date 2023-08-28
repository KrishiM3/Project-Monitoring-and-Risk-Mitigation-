import bcrypt
import boto3
import simplejson as json
from boto3.dynamodb.conditions import Key, Attr
from botocore.exceptions import ClientError
from boto3.dynamodb.types import TypeDeserializer

dynamodb = boto3.client('dynamodb')
table_name = 'Project'

salt = b'$2b$12$0qVXKTehuDvinJqboCmEKO'

def lambda_handler(event, context):
    # return {"statusCode": 400, "message": json.dumps("Project with same name already exists")}
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
            },
            ConditionExpression='attribute_not_exists(project_id)'
        )
        
        budget = event.get('budget')
        money_spent = event.get('money_spent')
        team_size = event.get('team_size')
        team_skill = event.get('team_skill')
        total_days = event.get('total_days')
        salary = event.get('salary')
        dynamodb.put_item(
            TableName="Project_Metrics",
            Item={
                'budget': {'N': str(budget)},
                'communication': {'N': '5'},
                'days_passed': {'N': '50'},
                'git_bugs': {'N': '25'},
                'lateness': {'N': '7'},
                'money_spent': {'N': str(money_spent)},
                'parties_involved': {'N': '4'},
                'project_progression': {'N': '0.5'},
                'scope_creep': {'N': '25'},
                'salary': {'N': str(salary)},
                'team_size': {'N': str(team_size)},
                'team_skill': {'N': str(team_skill)},
                'total_days': {'N': str(total_days)},
                'project_id': {'S': project_id}
            }
        );
        return {"code": 200, "message": "Project added successfully"}
    except dynamodb.exceptions.ConditionalCheckFailedException:
        return {"code": 400, "message": f"Project with same name already exists"}
    except Exception as e:
        return {"code": 500, "message": f"An unexpected error occurred while adding project: {e}"}