"""
Lambda Function: startup-investor-platform-send-email-notif
Purpose: Send email with actual startup recommendations via SES
"""

import json
import boto3
from botocore.exceptions import ClientError

ses = boto3.client('ses', region_name='eu-north-1')
dynamodb = boto3.resource('dynamodb')

STARTUPS_TABLE = 'startup-investor-platform-dev-startups'

def get_startup_details(startup_ids):
    """Fetch full startup details from DynamoDB"""
    table = dynamodb.Table(STARTUPS_TABLE)
    startups = []
    
    for startup_id in startup_ids:
        try:
            response = table.get_item(Key={'startup_id': startup_id})
            if 'Item' in response:
                startups.append(response['Item'])
        except Exception as e:
            print(f"Error fetching startup {startup_id}: {str(e)}")
    
    return startups

def format_startup_html(startup):
    """Format a single startup as HTML"""
    website_link = ''
    if startup.get('website'):
        website_link = f'<p style="margin-top: 15px;"><a href="{startup.get("website")}" style="color: #3498db; text-decoration: none;">Visit Website →</a></p>'
    
    html = f"""
    <div style="border: 1px solid #e0e0e0; border-radius: 8px; padding: 20px; margin-bottom: 20px; background-color: #ffffff;">
        <h2 style="color: #2c3e50; margin-top: 0;">{startup.get('name', 'Unknown')}</h2>
        <div style="margin-bottom: 10px;">
            <span style="display: inline-block; background-color: #3498db; color: white; padding: 5px 10px; border-radius: 4px; font-size: 12px; margin-right: 5px;">
                {startup.get('industry', 'N/A')}
            </span>
            <span style="display: inline-block; background-color: #2ecc71; color: white; padding: 5px 10px; border-radius: 4px; font-size: 12px;">
                {startup.get('funding_stage', 'N/A')}
            </span>
        </div>
        <p style="color: #555; line-height: 1.6;">{startup.get('description', 'No description available.')}</p>
        <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 10px; margin-top: 15px; padding-top: 15px; border-top: 1px solid #e0e0e0;">
            <div>
                <strong style="color: #7f8c8d;">Location:</strong> {startup.get('location', 'N/A')}
            </div>
            <div>
                <strong style="color: #7f8c8d;">Founded:</strong> {startup.get('founded_year', 'N/A')}
            </div>
            <div>
                <strong style="color: #7f8c8d;">Funding:</strong> {startup.get('funding_amount', 'N/A')}
            </div>
            <div>
                <strong style="color: #7f8c8d;">Team Size:</strong> {startup.get('team_size', 'N/A')}
            </div>
        </div>
        {website_link}
    </div>
    """
    return html

def create_email_html(startups, investor_email):
    """Create the full HTML email with all recommendations"""
    
    if not startups:
        startups_html = '<p style="color: #e74c3c;">No matching startups found. Try updating your preferences to broaden your search.</p>'
    else:
        startups_html = '\n'.join([format_startup_html(startup) for startup in startups])
    
    plural = '' if len(startups) == 1 else 's'
    
    html_body = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
    </head>
    <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333; max-width: 800px; margin: 0 auto; padding: 20px; background-color: #f4f4f4;">
        <div style="background-color: #2c3e50; color: white; padding: 30px; text-align: center; border-radius: 8px 8px 0 0;">
            <h1 style="margin: 0; font-size: 28px;">🚀 Your Startup Recommendations</h1>
            <p style="margin: 10px 0 0 0; font-size: 16px; opacity: 0.9;">Personalized matches based on your preferences</p>
        </div>
        
        <div style="background-color: white; padding: 30px; border-radius: 0 0 8px 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1);">
            <p style="font-size: 16px; margin-bottom: 20px;">Hi there! 👋</p>
            
            <p style="font-size: 16px; margin-bottom: 30px;">
                We've found <strong style="color: #2ecc71;">{len(startups)} startup{plural}</strong> that match your investment preferences. 
                Here are your personalized recommendations:
            </p>
            
            {startups_html}
            
            <div style="margin-top: 30px; padding: 20px; background-color: #ecf0f1; border-radius: 8px; text-align: center;">
                <p style="margin: 0 0 15px 0; font-size: 16px;">Want to see more details or update your preferences?</p>
                <a href="http://localhost:3000" 
                   style="display: inline-block; background-color: #3498db; color: white; padding: 12px 30px; text-decoration: none; border-radius: 5px; font-weight: bold;">
                    Visit Your Dashboard
                </a>
            </div>
            
            <div style="margin-top: 30px; padding-top: 20px; border-top: 1px solid #e0e0e0; font-size: 14px; color: #7f8c8d;">
                <p><strong>Need help?</strong> Reply to this email</p>
                <p style="margin-top: 10px; font-size: 12px;">
                    You received this email because you requested startup recommendations on the Startup Investor Platform.
                </p>
            </div>
        </div>
        
        <div style="text-align: center; margin-top: 20px; font-size: 12px; color: #7f8c8d;">
            <p>© 2025 Startup Investor Platform. All rights reserved.</p>
        </div>
    </body>
    </html>
    """
    
    return html_body

def lambda_handler(event, context):
    """
    Send email with startup recommendations
    """
    
    print(f"Received event: {json.dumps(event)}")
    
    try:
        investor_id = event.get('investor_id')
        email = event.get('email')
        matches = event.get('matches', [])
        
        if not email:
            raise ValueError("Email address is required")
        
        if not matches:
            print("No matches found, but sending email anyway")
        
        print(f"Sending recommendations to {email} for investor {investor_id}")
        print(f"Number of matches: {len(matches)}")
        
        # Fetch full startup details
        startups = get_startup_details(matches)
        print(f"Retrieved {len(startups)} startup details")
        
        # Create email content
        html_body = create_email_html(startups, email)
        
        # Plain text version - FIXED to avoid f-string backslash issue
        startup_list = '\n'.join([
            f"- {s.get('name', 'Unknown')} ({s.get('industry', 'N/A')}) - {s.get('funding_stage', 'N/A')}"
            for s in startups
        ])
        
        plural = 's' if len(startups) != 1 else ''
        
        text_body = f"""Hi there!

Your startup recommendations are ready!

We found {len(startups)} startup{plural} that match your investment preferences.

{startup_list}

Visit your dashboard to see full details: http://localhost:3000

Best regards,
The Startup Investor Platform Team"""
        
        # Send email via SES - USE YOUR VERIFIED EMAIL
        sender_email = "nerea.ugarte@alumni.esade.edu"
        
        subject_plural = "s" if len(startups) != 1 else ""
        
        response = ses.send_email(
            Source=sender_email,
            Destination={
                'ToAddresses': [email]
            },
            Message={
                'Subject': {
                    'Data': f'🚀 {len(startups)} Startup Recommendation{subject_plural} for You!',
                    'Charset': 'UTF-8'
                },
                'Body': {
                    'Text': {
                        'Data': text_body,
                        'Charset': 'UTF-8'
                    },
                    'Html': {
                        'Data': html_body,
                        'Charset': 'UTF-8'
                    }
                }
            }
        )
        
        print(f"Email sent successfully! MessageId: {response['MessageId']}")
        
        return {
            'statusCode': 200,
            'body': json.dumps({
                'message': 'Email sent successfully',
                'messageId': response['MessageId'],
                'recipientCount': len(startups)
            })
        }
        
    except ClientError as e:
        error_message = e.response['Error']['Message']
        print(f"SES Error: {error_message}")
        
        return {
            'statusCode': 500,
            'body': json.dumps({
                'error': f'Failed to send email: {error_message}'
            })
        }
        
    except Exception as e:
        print(f"Unexpected error: {str(e)}")
        import traceback
        traceback.print_exc()
        
        return {
            'statusCode': 500,
            'body': json.dumps({
                'error': f'Internal error: {str(e)}'
            })
        }

