import bcrypt
import boto3
from boto3.dynamodb.conditions import Key, Attr
from botocore.exceptions import ClientError
from boto3.dynamodb.types import TypeDeserializer

dynamodb = boto3.client('dynamodb')
table_name = 'Users'

salt = b'$2b$12$0qVXKTehuDvinJqboCmEKO'

def lambda_handler(event, context):
    email = event.get('email')
    password = (event.get('password')).encode('utf-8')
    hashed_password = (bcrypt.hashpw(password, salt)).decode('utf-8')
    try:
        dynamodb.put_item(
            TableName=table_name,
            Item={
                'email': {'S': email},
                'password_hash': {'S': hashed_password},
            },
            ConditionExpression='attribute_not_exists(email)', #currently just sign up, not login
        )
    except dynamodb.exceptions.ConditionalCheckFailedException:
        return {"code": 400, "message": f"User with same email already exists"}
    except Exception as e:
        return {"code": 500, "message": f"An unexpected error occurred while adding user: {e}"}
    else:
        return {"code": 200, "message": "User added successfully"}
