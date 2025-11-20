"""
Lambda Function: startup-investor-platform-dev-trigger-workflow
Purpose: Receives API Gateway requests and starts Step Functions state machine execution
"""

import json
import boto3
import os
from datetime import datetime

stepfunctions = boto3.client('stepfunctions')

def lambda_handler(event, context):
    """
    Triggers the startup matching Step Functions state machine
    
    Expected input from API Gateway:
    {
        "body": "{\"investor_id\": \"user123\", \"email\": \"user@example.com\"}"
    }
    """
    
    print(f"Received event: {json.dumps(event)}")
    
    try:
        # Parse the incoming request body
        if isinstance(event.get('body'), str):
            body = json.loads(event['body'])
        else:
            body = event.get('body', {})
        
        investor_id = body.get('investor_id')
        email = body.get('email')
        
        # Validate required fields
        if not investor_id:
            return {
                'statusCode': 400,
                'headers': {
                    'Access-Control-Allow-Origin': '*',
                    'Content-Type': 'application/json'
                },
                'body': json.dumps({
                    'error': 'Missing required field: investor_id'
                })
            }
        
        if not email:
            return {
                'statusCode': 400,
                'headers': {
                    'Access-Control-Allow-Origin': '*',
                    'Content-Type': 'application/json'
                },
                'body': json.dumps({
                    'error': 'Missing required field: email'
                })
            }
        
        # Get the state machine ARN from environment variable
        state_machine_arn = os.environ.get('STATE_MACHINE_ARN')
        
        if not state_machine_arn:
            # If not set as environment variable, you can hardcode it here temporarily
            # Get the ARN from your Step Functions console
            return {
                'statusCode': 500,
                'headers': {
                    'Access-Control-Allow-Origin': '*',
                    'Content-Type': 'application/json'
                },
                'body': json.dumps({
                    'error': 'STATE_MACHINE_ARN not configured. Please set environment variable.'
                })
            }
        
        print(f"Starting execution for investor: {investor_id}, email: {email}")
        
        # Prepare input for Step Functions
        step_functions_input = {
            'investor_id': investor_id,
            'email': email
        }
        
        # Start the Step Functions execution
        response = stepfunctions.start_execution(
            stateMachineArn=state_machine_arn,
            name=f"matching-{investor_id}-{int(datetime.now().timestamp())}",  # Unique execution name
            input=json.dumps(step_functions_input)
        )
        
        print(f"Step Functions execution started: {response['executionArn']}")
        
        # Return success response
        return {
            'statusCode': 200,
            'headers': {
                'Access-Control-Allow-Origin': '*',
                'Content-Type': 'application/json'
            },
            'body': json.dumps({
                'message': 'Matching process started successfully',
                'executionArn': response['executionArn'],
                'startDate': response['startDate'].isoformat() if 'startDate' in response else None
            })
        }
        
    except stepfunctions.exceptions.ExecutionAlreadyExists:
        return {
            'statusCode': 409,
            'headers': {
                'Access-Control-Allow-Origin': '*',
                'Content-Type': 'application/json'
            },
            'body': json.dumps({
                'error': 'An execution is already in progress. Please wait a moment and try again.'
            })
        }
        
    except Exception as e:
        print(f"Error starting Step Functions execution: {str(e)}")
        import traceback
        traceback.print_exc()
        
        return {
            'statusCode': 500,
            'headers': {
                'Access-Control-Allow-Origin': '*',
                'Content-Type': 'application/json'
            },
            'body': json.dumps({
                'error': f'Internal server error: {str(e)}'
            })
        }


# For local testing
if __name__ == "__main__":
    test_event = {
        'body': json.dumps({
            'investor_id': 'test-user-123',
            'email': 'test@example.com'
        })
    }
    
    result = lambda_handler(test_event, None)
    print(json.dumps(result, indent=2))

