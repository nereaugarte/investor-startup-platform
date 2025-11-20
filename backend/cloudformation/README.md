# Backend Infrastructure - CloudFormation

This directory contains CloudFormation templates for deploying backend infrastructure.

## Templates

### `backend-infrastructure.yaml`
Main backend infrastructure stack including:
- **Cognito User Pool** - User authentication
- **DynamoDB Tables** - Startups and Investors tables
- **S3 Bucket** - Assets storage
- **SNS Topic** - Notifications
- **IAM Role** - Lambda execution role with permissions

## Deployment

### Prerequisites
- AWS CLI configured
- Appropriate IAM permissions
- Region: `eu-north-1`

### Deploy Stack

```bash
# Create new stack
aws cloudformation create-stack \
  --stack-name startup-investor-platform-dev \
  --template-body file://backend-infrastructure.yaml \
  --capabilities CAPABILITY_IAM \
  --region eu-north-1

# Update existing stack
aws cloudformation update-stack \
  --stack-name startup-investor-platform-dev \
  --template-body file://backend-infrastructure.yaml \
  --capabilities CAPABILITY_IAM \
  --region eu-north-1
```

### Check Stack Status

```bash
aws cloudformation describe-stacks \
  --stack-name startup-investor-platform-dev \
  --region eu-north-1
```

### View Stack Outputs

```bash
aws cloudformation describe-stacks \
  --stack-name startup-investor-platform-dev \
  --query 'Stacks[0].Outputs' \
  --region eu-north-1 \
  --output table
```

## Stack Outputs

The stack provides these outputs:
- `UserPoolId` - Cognito User Pool ID
- `UserPoolClientId` - Cognito Client ID
- `StartupsTableName` - DynamoDB Startups table name
- `InvestorsTableName` - DynamoDB Investors table name
- `BucketName` - S3 Assets bucket name
- `SNSTopicArn` - SNS Topic ARN
- `LambdaRoleArn` - IAM Role ARN for Lambda functions

## Notes

- Stack name: `startup-investor-platform-dev`
- Region: `eu-north-1`
- Environment: `dev` (can be parameterized for staging/prod)

## Related

- Frontend infrastructure: `../../frontend/frontend-infrastructure.yaml`
- DynamoDB schemas: `../dynamodb-schemas/`

