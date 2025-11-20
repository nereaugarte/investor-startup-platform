import json
import os
import boto3
from decimal import Decimal
from datetime import datetime

dynamodb = boto3.resource('dynamodb')
ses_client = boto3.client('ses')

STARTUPS_TABLE = os.environ['STARTUPS_TABLE']
INVESTORS_TABLE = os.environ['INVESTORS_TABLE']
# Updated to use your verified email
SENDER_EMAIL = os.environ.get('SENDER_EMAIL', 'nerea.ugarte@alumni.esade.edu')

def decimal_default(obj):
    if isinstance(obj, Decimal):
        return float(obj)
    raise TypeError

def lambda_handler(event, context):
    startups_table = dynamodb.Table(STARTUPS_TABLE)
    investors_table = dynamodb.Table(INVESTORS_TABLE)
    
    # Check if specific investor requested (from API call)
    requested_investor_id = None
    if event.get('body'):
        try:
            body = json.loads(event['body']) if isinstance(event['body'], str) else event['body']
            requested_investor_id = body.get('investor_id')
            print(f"Matching requested for specific investor: {requested_investor_id}")
        except:
            pass
    
    # Get all investors
    investors_response = investors_table.scan()
    investors = investors_response.get('Items', [])
    
    # Filter to specific investor if requested
    if requested_investor_id:
        investors = [inv for inv in investors if inv.get('investor_id') == requested_investor_id or inv.get('email') == requested_investor_id]
        print(f"Filtered to {len(investors)} investor(s)")
    
    if not investors:
        print("No investors found")
        return {
            'statusCode': 200,
            'matchesFound': False,
            'body': json.dumps({'message': 'No investors found', 'total_matches': 0})
        }
    
    # Get all startups
    startups_response = startups_table.scan()
    startups = startups_response.get('Items', [])
    
    if not startups:
        print("No startups found")
        return {
            'statusCode': 200,
            'matchesFound': False,
            'body': json.dumps({'message': 'No startups found', 'total_matches': 0})
        }
    
    print(f"Processing {len(investors)} investors and {len(startups)} startups")
    
    total_matches = 0
    all_matches = []
    
    for investor in investors:
        investor_id = investor.get('investor_id', 'Unknown')
        investor_name = investor.get('name', investor_id)
        investor_email = investor.get('email')
        
        # Get preferences
        preferred_industries = investor.get('preferred_industries', [])
        preferred_stages = investor.get('preferred_funding_stages', [])
        
        print(f"\nMatching for {investor_email}")
        print(f"  Industries: {preferred_industries}")
        print(f"  Stages: {preferred_stages}")
        
        # STRICTER MATCHING: If no preferences, don't match anything
        if not preferred_industries and not preferred_stages:
            print("  ⚠️  No preferences set - skipping")
            # IMPORTANT: Clear old recommendations if preferences removed
            try:
                investors_table.update_item(
                    Key={'investor_id': investor_id},
                    UpdateExpression='SET recommendations = :empty, last_matched = :timestamp',
                    ExpressionAttributeValues={
                        ':empty': [],
                        ':timestamp': datetime.utcnow().isoformat()
                    }
                )
                print(f"  ✅ Cleared recommendations for investor with no preferences")
            except Exception as e:
                print(f"  ❌ Error clearing recommendations: {str(e)}")
            continue
        
        matches = []
        
        for startup in startups:
            match_score = 0
            industry_match = False
            stage_match = False
            
            startup_industry = startup.get('industry', '')
            startup_stage = startup.get('funding_stage', '')
            startup_id = startup.get('startup_id', '')
            
            # Industry matching - STRICT
            if preferred_industries:
                for pref_industry in preferred_industries:
                    # Exact or substring match
                    if pref_industry.lower() in startup_industry.lower() or \
                       startup_industry.lower() in pref_industry.lower():
                        industry_match = True
                        match_score += 50  # 50 points for industry match
                        break
            
            # Funding stage matching - STRICT
            if preferred_stages:
                if startup_stage in preferred_stages:
                    stage_match = True
                    match_score += 50  # 50 points for stage match
            
            # STRICT MATCHING: REQUIRE BOTH industry AND stage to match
            # Only add if we have preferences for both and they both match
            has_industry_pref = len(preferred_industries) > 0
            has_stage_pref = len(preferred_stages) > 0
            
            # If user set both preferences, require both to match
            if has_industry_pref and has_stage_pref:
                if industry_match and stage_match:
                    matches.append({
                        'startup_id': startup_id,
                        'name': startup.get('name', 'Unknown'),
                        'industry': startup_industry,
                        'funding_stage': startup_stage,
                        'description': startup.get('description', ''),
                        'location': startup.get('location', ''),
                        'website': startup.get('website', ''),
                        'funding_amount': startup.get('funding_amount', 'N/A'),
                        'match_score': match_score,
                        'industry_match': industry_match,
                        'stage_match': stage_match
                    })
            # If user only set one preference, match on that one
            elif has_industry_pref and industry_match:
                matches.append({
                    'startup_id': startup_id,
                    'name': startup.get('name', 'Unknown'),
                    'industry': startup_industry,
                    'funding_stage': startup_stage,
                    'description': startup.get('description', ''),
                    'location': startup.get('location', ''),
                    'website': startup.get('website', ''),
                    'funding_amount': startup.get('funding_amount', 'N/A'),
                    'match_score': match_score,
                    'industry_match': industry_match,
                    'stage_match': stage_match
                })
            elif has_stage_pref and stage_match:
                matches.append({
                    'startup_id': startup_id,
                    'name': startup.get('name', 'Unknown'),
                    'industry': startup_industry,
                    'funding_stage': startup_stage,
                    'description': startup.get('description', ''),
                    'location': startup.get('location', ''),
                    'website': startup.get('website', ''),
                    'funding_amount': startup.get('funding_amount', 'N/A'),
                    'match_score': match_score,
                    'industry_match': industry_match,
                    'stage_match': stage_match
                })
        
        print(f"  Found {len(matches)} matches")
        
        # Sort by match score
        matches.sort(key=lambda x: x['match_score'], reverse=True)
        
        # ===== KEY FIX: WRITE TO DYNAMODB (REPLACES OLD DATA) =====
        try:
            # Prepare recommendations for storage (simplified version)
            stored_recommendations = [
                {
                    'startup_id': m['startup_id'],
                    'name': m['name'],
                    'industry': m['industry'],
                    'funding_stage': m['funding_stage'],
                    'match_score': m['match_score']
                }
                for m in matches
            ]
            
            # UPDATE investor record with NEW recommendations
            # This REPLACES the old recommendations array completely
            investors_table.update_item(
                Key={'investor_id': investor_id},
                UpdateExpression='SET recommendations = :recs, last_matched = :timestamp',
                ExpressionAttributeValues={
                    ':recs': stored_recommendations,
                    ':timestamp': datetime.utcnow().isoformat()
                }
            )
            print(f"  ✅ Stored {len(stored_recommendations)} recommendations in DynamoDB")
        except Exception as e:
            print(f"  ❌ Error storing recommendations in DynamoDB: {str(e)}")
        # ========================================================
        
        # Send email if matches found
        if matches and investor_email:
            total_matches += len(matches)
            
            all_matches.append({
                'investor_email': investor_email,
                'match_count': len(matches),
                'top_matches': matches[:5]
            })
            
            try:
                # Create HTML email message
                html_message = f"""<html>
<head></head>
<body>
<h2>Hello {investor_name}!</h2>
<p>We found <strong>{len(matches)}</strong> startup(s) matching your investment preferences.</p>

<h3>Top Matches:</h3>
"""
                
                # Add top 5 matches with details
                for i, match in enumerate(matches[:5], 1):
                    match_icons = []
                    if match['industry_match']:
                        match_icons.append('🎯 Industry Match')
                    if match['stage_match']:
                        match_icons.append('📊 Stage Match')
                    
                    html_message += f"""
<div style="border: 1px solid #ddd; padding: 15px; margin: 10px 0; border-radius: 8px;">
<h4>{i}. {match['name']} - {match['industry']}</h4>
<p><strong>Stage:</strong> {match['funding_stage']} | <strong>Funding:</strong> {match['funding_amount']}</p>
<p><strong>Location:</strong> {match['location']}</p>
<p><strong>Match Score:</strong> {match['match_score']}% | <strong>Why matched:</strong> {' | '.join(match_icons)}</p>
<p>{match['description'][:150]}...</p>
<p><a href="{match['website']}" target="_blank">Visit Website</a></p>
</div>
"""
                
                if len(matches) > 5:
                    html_message += f"<p><em>... and {len(matches) - 5} more matches!</em></p>"
                
                html_message += f"""
<hr>
<p><strong>Your preferences:</strong></p>
<ul>
<li><strong>Industries:</strong> {', '.join(preferred_industries) if preferred_industries else 'Not set'}</li>
<li><strong>Stages:</strong> {', '.join(preferred_stages) if preferred_stages else 'Not set'}</li>
</ul>

<p>Visit the <a href="https://your-vercel-url.vercel.app">Startup Investor Platform</a> to explore all your matches!</p>

<p style="color: #666; font-size: 12px;">This is an automated notification from Startup Investor Platform.</p>
</body>
</html>"""
                
                # Plain text version
                text_message = f"""Hello {investor_name}!

We found {len(matches)} startup(s) matching your investment preferences.

TOP MATCHES:

"""
                for i, match in enumerate(matches[:5], 1):
                    text_message += f"""{i}. {match['name']} - {match['industry']}
   Stage: {match['funding_stage']} | Funding: {match['funding_amount']}
   Match Score: {match['match_score']}%
   Location: {match['location']}
   {match['description'][:120]}...
   Website: {match['website']}
   
"""
                
                # Send via SES directly to investor
                response = ses_client.send_email(
                    Source=SENDER_EMAIL,
                    Destination={'ToAddresses': [investor_email]},
                    Message={
                        'Subject': {'Data': f'🚀 {len(matches)} Startup Matches Found!'},
                        'Body': {
                            'Text': {'Data': text_message},
                            'Html': {'Data': html_message}
                        }
                    }
                )
                
                print(f"  ✅ Email sent to {investor_email} (MessageId: {response['MessageId']})")
                
            except Exception as e:
                print(f"  ❌ Error sending email: {str(e)}")
        else:
            if not matches:
                print(f"  No matches found for this investor")
            if not investor_email:
                print(f"  No email address for this investor")
    
    # Return summary
    result = {
        'statusCode': 200,
        'matchesFound': total_matches > 0,
        'body': json.dumps({
            'message': 'Matching completed successfully',
            'total_matches': total_matches,
            'investors_processed': len(investors),
            'matches_summary': all_matches
        }, default=decimal_default)
    }
    
    print(f"\n✅ Complete: {total_matches} matches for {len(investors)} investors")
    
    return result

