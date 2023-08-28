import json

def lambda_handler(event, context):
    event['response'] = {
        'autoConfirmUser': True,
        'autoVerifyEmail': False,
        'autoVerifyPhone': False
    }

    return event