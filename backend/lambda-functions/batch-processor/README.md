# Batch Processor Lambda

## Purpose
Enables daily automated email recommendations for users who opt-in.

## How It Works
1. EventBridge rule triggers this Lambda hourly (rate: 1 hour)
2. Lambda queries DynamoDB for users with `daily_recommendations=true`
3. For each user, checks if current time matches their preferred time
4. If yes, triggers the Step Functions state machine
5. Step Functions handles the matching and email sending

## Deployment
Would be deployed with:
- EventBridge Rule (schedule: rate(1 hour))
- IAM permissions for DynamoDB:Scan and States:StartExecution

## Environment Variables
- `PREFERENCES_TABLE`: Name of investor preferences DynamoDB table
- `STATE_MACHINE_ARN`: ARN of the matching state machine

## Why This Architecture?
- Reuses existing Step Functions workflow
- Decouples scheduling from matching logic
- Scales automatically with number of users
- Cost-effective (only runs when needed)
