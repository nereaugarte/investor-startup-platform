# Step Functions - Startup Matching Workflow

This directory contains the Step Functions state machine definition and CloudFormation template for the startup matching workflow.

## Overview

The Step Functions workflow orchestrates the startup matching process:

1. **MatchStartups** - Runs the matching algorithm Lambda
2. **CheckMatches** - Checks if matches were found
3. **SendNotifications** - Sends email via SES if matches found
4. **NoMatchesFound** - End state if no matches

## Workflow Diagram

```
┌─────────────────┐
│  MatchStartups  │ (Lambda: startup-matcher)
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  CheckMatches   │ (Choice State)
└────┬────────┬───┘
     │        │
Matches?      No
     │        │
     ▼        ▼
┌─────────────┐  ┌──────────────┐
│SendEmail    │  │NoMatchesFound│
│(Lambda)     │  │(Pass State)   │
└─────────────┘  └──────────────┘
```

## Files

- **`startup-matcher-workflow.json`** - State machine definition (JSON format)
- **`step-functions-infrastructure.yaml`** - CloudFormation template
- **`deploy-stepfunctions.sh`** - Deployment script

## State Machine Details

### States

1. **MatchStartups** (Task)
   - **Lambda**: `startup-investor-platform-dev-startup-matcher`
   - **Purpose**: Runs matching algorithm
   - **Retry**: 3 attempts with exponential backoff
   - **Error Handling**: Catches errors and goes to NoMatchesFound

2. **CheckMatches** (Choice)
   - **Condition**: Checks if `$.matchesFound` is `true`
   - **If true**: Goes to SendNotifications
   - **If false**: Goes to NoMatchesFound

3. **SendNotifications** (Task)
   - **Lambda**: `startup-investor-platform-dev-send-email-notif`
   - **Purpose**: Sends email with recommendations
   - **Retry**: 3 attempts with exponential backoff

4. **NoMatchesFound** (Pass)
   - **Purpose**: End state when no matches found
   - **Result**: Returns message indicating no matches

## Input Format

```json
{
  "investor_id": "user@example.com",
  "email": "user@example.com",
  "trigger_type": "manual" | "scheduled_daily"
}
```

## Output Format

**Success (with matches):**
```json
{
  "statusCode": 200,
  "message": "Email sent successfully",
  "messageId": "010001...",
  "recipientCount": 5
}
```

**No matches:**
```json
{
  "message": "No matches found for investor",
  "matchesFound": false
}
```

## Deployment

### Prerequisites

1. Lambda functions must be deployed first:
   - `startup-investor-platform-dev-startup-matcher`
   - `startup-investor-platform-dev-send-email-notif`

2. Get Lambda ARNs:
   ```bash
   aws lambda get-function \
     --function-name startup-investor-platform-dev-startup-matcher \
     --region eu-north-1 \
     --query 'Configuration.FunctionArn' \
     --output text
   ```

### Deploy with CloudFormation

```bash
cd backend/step-functions

# Deploy
./deploy-stepfunctions.sh create \
  --match-lambda-arn "arn:aws:lambda:eu-north-1:ACCOUNT:function:startup-investor-platform-dev-startup-matcher" \
  --email-lambda-arn "arn:aws:lambda:eu-north-1:ACCOUNT:function:startup-investor-platform-dev-send-email-notif"
```

### Update Existing

```bash
./deploy-stepfunctions.sh update \
  --match-lambda-arn "arn:..." \
  --email-lambda-arn "arn:..."
```

## Usage

### Trigger from Lambda

```python
import boto3

stepfunctions = boto3.client('stepfunctions')

response = stepfunctions.start_execution(
    stateMachineArn='arn:aws:states:eu-north-1:ACCOUNT:stateMachine:startup-investor-platform-dev-startup-matcher',
    name=f"matching-{investor_id}-{timestamp}",
    input=json.dumps({
        'investor_id': investor_id,
        'email': email
    })
)
```

### Trigger from API Gateway

The workflow is triggered by:
- **Manual**: User clicks "Get Recommendations" → API Gateway → Lambda → Step Functions
- **Scheduled**: EventBridge → Batch Processor Lambda → Step Functions

## Monitoring

### CloudWatch Logs

Logs are available at:
```
/aws/stepfunctions/startup-investor-platform-dev-startup-matcher
```

### View Executions

```bash
aws stepfunctions list-executions \
  --state-machine-arn "arn:aws:states:eu-north-1:ACCOUNT:stateMachine:startup-investor-platform-dev-startup-matcher" \
  --region eu-north-1
```

### Check Execution Status

```bash
aws stepfunctions describe-execution \
  --execution-arn "EXECUTION_ARN" \
  --region eu-north-1
```

## IAM Permissions

The Step Functions role needs:
- `lambda:InvokeFunction` on both Lambda functions
- CloudWatch Logs permissions (for logging)

## Cost

Step Functions pricing:
- **State transitions**: $0.000025 per transition
- **Free tier**: 4,000 free transitions per month

Typical workflow: ~4 transitions = $0.0001 per execution

## Troubleshooting

### Common Issues

1. **Lambda not found**
   - Ensure Lambda functions are deployed
   - Check ARNs in CloudFormation parameters

2. **Execution fails**
   - Check CloudWatch Logs for Step Functions
   - Check Lambda function logs
   - Verify IAM permissions

3. **No email sent**
   - Check SES permissions
   - Verify email address is verified in SES
   - Check Lambda function logs

## Related

- Lambda Functions: `../lambda-functions/`
- CloudFormation: `../cloudformation/`
- Architecture: `../../docs/ARCHITECTURE.md`

