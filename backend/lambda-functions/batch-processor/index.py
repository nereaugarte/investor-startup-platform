"""
Batch Processor Lambda - Daily Recommendations

This Lambda would be triggered by EventBridge hourly to send
daily recommendations to users who have opted in.

How it works:
1. Query DynamoDB for users with daily_recommendations=true
2. Check each user's timezone and preferred time
3. If it's their preferred time, trigger Step Functions
4. Step Functions matches startups and sends email

Environment Variables needed:
- PREFERENCES_TABLE
- STATE_MACHINE_ARN
"""

import json
import boto3
from datetime import datetime

dynamodb = boto3.resource('dynamodb')
stepfunctions = boto3.client('stepfunctions')

def lambda_handler(event, context):
    """
    Main handler for batch processing daily recommendations
    """
    
    print(f"Batch processor triggered at {datetime.now()}")
    
    # Query users with daily recommendations enabled
    # For each user at their preferred time:
    #   - Trigger Step Functions with their preferences
    #   - Step Functions handles matching and email
    
    return {
        'statusCode': 200,
        'body': json.dumps({
            'message': 'Batch processing complete'
        })
    }
