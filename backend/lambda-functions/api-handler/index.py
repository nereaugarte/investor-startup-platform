import json
import os
import boto3
from boto3.dynamodb.conditions import Key
from decimal import Decimal

dynamodb = boto3.resource('dynamodb')
STARTUPS_TABLE = os.environ['STARTUPS_TABLE']
INVESTORS_TABLE = os.environ.get('INVESTORS_TABLE', 'startup-investor-platform-dev-investors')

def decimal_default(obj):
    if isinstance(obj, Decimal):
        return float(obj)
    raise TypeError

def cors_response(status_code, body):
    return {
        'statusCode': status_code,
        'headers': {
            'Content-Type': 'application/json',
            'Access-Control-Allow-Origin': '*',
            'Access-Control-Allow-Headers': 'Content-Type,Authorization',
            'Access-Control-Allow-Methods': 'GET,POST,OPTIONS'
        },
        'body': json.dumps(body, default=decimal_default)
    }

def lambda_handler(event, context):
    http_method = event.get('httpMethod', 'GET')
    path = event.get('path', '')
    resource = event.get('resource', '')
    
    print(f"Method: {http_method}, Path: {path}, Resource: {resource}")
    
    try:
        # Startups endpoints
        if http_method == 'GET' and '/startups' in path:
            if '{id}' in resource:
                return get_startup(event)
            else:
                return get_startups(event)
        
        elif http_method == 'POST' and 'contact' in path:
            return contact_startup(event)
        
        # Investor endpoints - NEW!
        elif http_method == 'POST' and resource == '/investors':
            return save_investor(event)
        
        elif http_method == 'GET' and '/investors/{id}' in resource:
            return get_investor(event)
        
        # Trigger matching endpoint
        elif http_method == 'POST' and resource == '/trigger-matching':
            return trigger_matching(event)
        
        else:
            return cors_response(404, {'error': 'Not found'})
    
    except Exception as e:
        print(f"Error: {str(e)}")
        return cors_response(500, {'error': str(e)})

def get_startups(event):
    table = dynamodb.Table(STARTUPS_TABLE)
    params = event.get('queryStringParameters') or {}
    industry = params.get('industry')
    limit = int(params.get('limit', 25))
    
    try:
        if industry:
            response = table.query(
                IndexName='IndustryIndex',
                KeyConditionExpression=Key('industry').eq(industry),
                Limit=limit
            )
        else:
            response = table.scan(Limit=limit)
        
        startups = response.get('Items', [])
        return cors_response(200, {
            'startups': startups,
            'count': len(startups)
        })
    
    except Exception as e:
        return cors_response(500, {'error': str(e)})

def get_startup(event):
    table = dynamodb.Table(STARTUPS_TABLE)
    startup_id = event['pathParameters']['id']
    
    try:
        response = table.get_item(Key={'startup_id': startup_id})
        
        if 'Item' not in response:
            return cors_response(404, {'error': 'Startup not found'})
        
        return cors_response(200, response['Item'])
    
    except Exception as e:
        return cors_response(500, {'error': str(e)})

def contact_startup(event):
    startup_id = event['pathParameters']['id']
    
    try:
        body = json.loads(event['body'])
    except:
        return cors_response(400, {'error': 'Invalid body'})
    
    print(f"Contact request for startup {startup_id}")
    return cors_response(200, {
        'message': 'Contact request sent',
        'startup_id': startup_id
    })

# NEW INVESTOR ENDPOINTS

def save_investor(event):
    """Save or update investor profile"""
    table = dynamodb.Table(INVESTORS_TABLE)
    
    try:
        body = json.loads(event['body'])
        
        # Validate required fields
        if 'investor_id' not in body or 'email' not in body:
            return cors_response(400, {'error': 'investor_id and email are required'})
        
        # Create investor item
        item = {
            'investor_id': body['investor_id'],
            'email': body['email'],
            'name': body.get('name', body['email']),
            'preferred_industries': body.get('preferred_industries', []),
            'preferred_funding_stages': body.get('preferred_funding_stages', []),
            'min_investment': body.get('min_investment', 0),
            'max_investment': body.get('max_investment', 10000000000),
            'created_at': body.get('created_at'),
            'updated_at': body.get('updated_at')
        }
        
        # Save to DynamoDB
        table.put_item(Item=item)
        
        print(f"✅ Saved investor profile for {body['email']}")
        
        return cors_response(200, {
            'message': 'Investor profile saved successfully',
            'investor_id': body['investor_id']
        })
    
    except json.JSONDecodeError:
        return cors_response(400, {'error': 'Invalid JSON in request body'})
    
    except Exception as e:
        print(f"❌ Error saving investor: {str(e)}")
        return cors_response(500, {'error': str(e)})

def get_investor(event):
    """Get investor profile by ID"""
    table = dynamodb.Table(INVESTORS_TABLE)
    
    try:
        investor_id = event['pathParameters']['id']
        
        print(f"Getting investor profile for: {investor_id}")
        
        response = table.get_item(Key={'investor_id': investor_id})
        
        if 'Item' not in response:
            print(f"Investor not found: {investor_id}")
            return cors_response(404, {'error': 'Investor not found'})
        
        print(f"✅ Found investor profile for {investor_id}")
        return cors_response(200, response['Item'])
    
    except Exception as e:
        print(f"❌ Error getting investor: {str(e)}")
        return cors_response(500, {'error': str(e)})

def trigger_matching(event):
    """Trigger the matching Lambda to send recommendations"""
    lambda_client = boto3.client('lambda')
    
    try:
        # Get investor_id from request body
        body = json.loads(event.get('body', '{}'))
        investor_id = body.get('investor_id')
        
        print(f"Triggering matching for investor: {investor_id}")
        
        # Invoke the matching Lambda with proper payload format
        response = lambda_client.invoke(
            FunctionName='startup-investor-platform-dev-startup-matcher',
            InvocationType='RequestResponse',
            Payload=json.dumps({
                'body': json.dumps({'investor_id': investor_id})
            })
        )
        
        # Parse response
        response_payload = json.loads(response['Payload'].read())
        
        print(f"Matching Lambda response: {response_payload}")
        
        # Extract result from response body
        if 'body' in response_payload:
            body_content = json.loads(response_payload['body'])
            return cors_response(200, body_content)
        else:
            return cors_response(200, response_payload)
    
    except Exception as e:
        print(f"❌ Error triggering matching: {str(e)}")
        return cors_response(500, {'error': str(e)})

