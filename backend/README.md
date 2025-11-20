# Backend Infrastructure

This directory contains all backend code and infrastructure for the Startup Investor Platform.

## Architecture

- **lambda-functions/** - All Lambda function code
- **step-functions/** - State machine definitions
- **cloudformation/** - Infrastructure as code templates
- **dynamodb-schemas/** - DynamoDB table schemas

## Lambda Functions

1. **api-handler** - REST API endpoint handler
2. **startup-matcher** - Matching algorithm implementation
3. **send-email-notif** - SES email sender
4. **trigger-workflow** - Step Functions trigger
5. **batch-processor** - EventBridge daily scheduler

See individual function READMEs for details.
