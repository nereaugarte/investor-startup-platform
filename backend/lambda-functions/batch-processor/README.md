# Batch Processor Lambda

Processes daily scheduled recommendations.

## Runtime
Python 3.11

## Trigger
EventBridge (hourly)

## Environment Variables
- PREFERENCES_TABLE
- STATE_MACHINE_ARN

## IAM Permissions
- dynamodb:Scan
- dynamodb:UpdateItem
- states:StartExecution
