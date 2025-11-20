"""
Lambda Function: investor-startup-platform-batch-processor
Purpose: Process daily scheduled recommendations for opted-in users
Triggered by: EventBridge (hourly)
"""

import json
import boto3
import os
from datetime import datetime, timedelta
from boto3.dynamodb.conditions import Attr

dynamodb = boto3.resource('dynamodb')
stepfunctions = boto3.client('stepfunctions')

# Configuration - YOU NEED TO SET THESE IN LAMBDA ENVIRONMENT VARIABLES
PREFERENCES_TABLE = os.environ.get('PREFERENCES_TABLE', 'startup-investor-platform-dev-investor-preferences')
STATE_MACHINE_ARN = os.environ.get('STATE_MACHINE_ARN', '')

def lambda_handler(event, context):
    """
    Main handler - triggered by EventBridge hourly
    Finds users who should receive daily recommendations now and triggers matching
    """
    
    print(f"=== Batch Processor Started at {datetime.utcnow().isoformat()} ===")
    
    if not STATE_MACHINE_ARN:
        print("ERROR: STATE_MACHINE_ARN not configured!")
        return {
            'statusCode': 500,
            'body': json.dumps({'error': 'STATE_MACHINE_ARN not configured'})
        }
    
    stats = {
        'users_checked': 0,
        'users_triggered': 0,
        'users_skipped': 0,
        'errors': 0
    }
    
    try:
        # Get all users with daily recommendations enabled
        users = get_users_with_daily_recommendations()
        stats['users_checked'] = len(users)
        
        print(f"Found {len(users)} users with daily_recommendations enabled")
        
        current_hour = datetime.utcnow().hour
        print(f"Current UTC hour: {current_hour}")
        
        # Process each user
        for user in users:
            try:
                investor_id = user.get('investor_id')
                email = user.get('email')
                preferred_time = user.get('preferred_time', '09:00')
                
                if not investor_id or not email:
                    print(f"Skipping user with missing data: {user.get('investor_id', 'unknown')}")
                    stats['users_skipped'] += 1
                    continue
                
                # Simple check: does preferred hour match current hour?
                # For MVP, we'll use UTC time (you can enhance with timezone later)
                preferred_hour = int(preferred_time.split(':')[0])
                
                # Check if already sent today
                last_sent = user.get('last_recommendation_sent')
                if last_sent:
                    last_sent_date = datetime.fromisoformat(last_sent.replace('Z', '+00:00'))
                    hours_since_last = (datetime.utcnow() - last_sent_date.replace(tzinfo=None)).total_seconds() / 3600
                    
                    if hours_since_last < 23:
                        print(f"Skipping {investor_id} - already sent {hours_since_last:.1f} hours ago")
                        stats['users_skipped'] += 1
                        continue
                
                # Check if this is their preferred hour
                if current_hour == preferred_hour:
                    print(f"✅ Triggering recommendations for {investor_id} ({email})")
                    
                    if trigger_step_functions(investor_id, email):
                        update_last_sent_timestamp(investor_id)
                        stats['users_triggered'] += 1
                    else:
                        stats['errors'] += 1
                else:
                    print(f"Skipping {investor_id} - preferred hour {preferred_hour}, current hour {current_hour}")
                    stats['users_skipped'] += 1
                    
            except Exception as e:
                print(f"Error processing user {user.get('investor_id', 'unknown')}: {str(e)}")
                stats['errors'] += 1
        
        # Log final stats
        print(f"=== Batch Processing Complete ===")
        print(f"Stats: {json.dumps(stats)}")
        
        return {
            'statusCode': 200,
            'body': json.dumps({
                'message': 'Batch processing complete',
                'stats': stats
            })
        }
        
    except Exception as e:
        print(f"FATAL ERROR in batch processor: {str(e)}")
        import traceback
        traceback.print_exc()
        
        return {
            'statusCode': 500,
            'body': json.dumps({
                'error': str(e),
                'stats': stats
            })
        }


def get_users_with_daily_recommendations():
    """Query DynamoDB for users with daily_recommendations enabled"""
    table = dynamodb.Table(PREFERENCES_TABLE)
    
    try:
        response = table.scan(
            FilterExpression=Attr('daily_recommendations').eq(True)
        )
        
        users = response.get('Items', [])
        
        # Handle pagination
        while 'LastEvaluatedKey' in response:
            response = table.scan(
                FilterExpression=Attr('daily_recommendations').eq(True),
                ExclusiveStartKey=response['LastEvaluatedKey']
            )
            users.extend(response.get('Items', []))
        
        return users
        
    except Exception as e:
        print(f"Error querying preferences: {str(e)}")
        return []


def trigger_step_functions(investor_id, email):
    """Trigger Step Functions state machine for a user"""
    try:
        execution_name = f"daily-{investor_id}-{int(datetime.utcnow().timestamp())}"
        
        response = stepfunctions.start_execution(
            stateMachineArn=STATE_MACHINE_ARN,
            name=execution_name,
            input=json.dumps({
                'investor_id': investor_id,
                'email': email,
                'trigger_type': 'scheduled_daily'
            })
        )
        
        print(f"✅ Started execution: {response['executionArn']}")
        return True
        
    except stepfunctions.exceptions.ExecutionAlreadyExists:
        print(f"⚠️ Execution already running for {investor_id}")
        return False
        
    except Exception as e:
        print(f"❌ Error triggering Step Functions for {investor_id}: {str(e)}")
        return False


def update_last_sent_timestamp(investor_id):
    """Update the last_recommendation_sent timestamp"""
    table = dynamodb.Table(PREFERENCES_TABLE)
    
    try:
        table.update_item(
            Key={'investor_id': investor_id},
            UpdateExpression='SET last_recommendation_sent = :timestamp',
            ExpressionAttributeValues={
                ':timestamp': datetime.utcnow().isoformat() + 'Z'
            }
        )
        print(f"Updated timestamp for {investor_id}")
        
    except Exception as e:
        print(f"Error updating timestamp for {investor_id}: {str(e)}")


# For testing
if __name__ == "__main__":
    # Test locally
    test_event = {
        'version': '0',
        'id': 'test-event',
        'detail-type': 'Scheduled Event',
        'source': 'aws.events'
    }
    
    result = lambda_handler(test_event, None)
    print(json.dumps(result, indent=2))

