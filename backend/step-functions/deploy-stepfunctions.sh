#!/bin/bash

# Deployment script for Step Functions state machine
# Usage: ./deploy-stepfunctions.sh [action] [options]

set -e

STACK_NAME="startup-investor-platform-stepfunctions-dev"
REGION="eu-north-1"
ENVIRONMENT="dev"
TEMPLATE_FILE="step-functions-infrastructure.yaml"

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

ACTION=${1:-status}

# Parse arguments
MATCH_LAMBDA_ARN=""
EMAIL_LAMBDA_ARN=""

while [[ $# -gt 0 ]]; do
    case $1 in
        --match-lambda-arn)
            MATCH_LAMBDA_ARN="$2"
            shift 2
            ;;
        --email-lambda-arn)
            EMAIL_LAMBDA_ARN="$2"
            shift 2
            ;;
        *)
            shift
            ;;
    esac
done

# Auto-detect Lambda ARNs if not provided
if [ -z "$MATCH_LAMBDA_ARN" ] || [ -z "$EMAIL_LAMBDA_ARN" ]; then
    echo -e "${YELLOW}🔍 Auto-detecting Lambda function ARNs...${NC}"
    
    if [ -z "$MATCH_LAMBDA_ARN" ]; then
        MATCH_LAMBDA_ARN=$(aws lambda get-function \
            --function-name "startup-investor-platform-${ENVIRONMENT}-startup-matcher" \
            --region "$REGION" \
            --query 'Configuration.FunctionArn' \
            --output text 2>/dev/null || echo "")
        
        if [ -z "$MATCH_LAMBDA_ARN" ]; then
            echo -e "${RED}❌ Could not find startup-matcher Lambda function${NC}"
            echo -e "${YELLOW}💡 Please provide --match-lambda-arn parameter${NC}"
            exit 1
        fi
        echo -e "${GREEN}✅ Found match Lambda: ${MATCH_LAMBDA_ARN}${NC}"
    fi
    
    if [ -z "$EMAIL_LAMBDA_ARN" ]; then
        EMAIL_LAMBDA_ARN=$(aws lambda get-function \
            --function-name "startup-investor-platform-${ENVIRONMENT}-send-email-notif" \
            --region "$REGION" \
            --query 'Configuration.FunctionArn' \
            --output text 2>/dev/null || echo "")
        
        if [ -z "$EMAIL_LAMBDA_ARN" ]; then
            echo -e "${RED}❌ Could not find send-email-notif Lambda function${NC}"
            echo -e "${YELLOW}💡 Please provide --email-lambda-arn parameter${NC}"
            exit 1
        fi
        echo -e "${GREEN}✅ Found email Lambda: ${EMAIL_LAMBDA_ARN}${NC}"
    fi
fi

check_stack_exists() {
    aws cloudformation describe-stacks \
        --stack-name "$STACK_NAME" \
        --region "$REGION" \
        &> /dev/null
}

create_stack() {
    echo -e "${YELLOW}📦 Creating Step Functions stack...${NC}"
    
    if check_stack_exists; then
        echo -e "${RED}❌ Stack $STACK_NAME already exists!${NC}"
        echo -e "${YELLOW}💡 Use 'update' action to update existing stack${NC}"
        exit 1
    fi
    
    aws cloudformation create-stack \
        --stack-name "$STACK_NAME" \
        --template-body file://"$TEMPLATE_FILE" \
        --parameters \
            ParameterKey=Environment,ParameterValue="$ENVIRONMENT" \
            ParameterKey=MatchStartupsLambdaArn,ParameterValue="$MATCH_LAMBDA_ARN" \
            ParameterKey=SendEmailLambdaArn,ParameterValue="$EMAIL_LAMBDA_ARN" \
        --capabilities CAPABILITY_IAM \
        --region "$REGION" \
        --no-cli-pager
    
    echo -e "${GREEN}✅ Stack creation initiated${NC}"
    echo -e "${YELLOW}⏳ Waiting for stack creation to complete...${NC}"
    
    aws cloudformation wait stack-create-complete \
        --stack-name "$STACK_NAME" \
        --region "$REGION"
    
    echo -e "${GREEN}🎉 Stack created successfully!${NC}"
    show_outputs
}

update_stack() {
    echo -e "${YELLOW}🔄 Updating Step Functions stack...${NC}"
    
    if ! check_stack_exists; then
        echo -e "${RED}❌ Stack $STACK_NAME does not exist!${NC}"
        echo -e "${YELLOW}💡 Use 'create' action to create new stack${NC}"
        exit 1
    fi
    
    aws cloudformation update-stack \
        --stack-name "$STACK_NAME" \
        --template-body file://"$TEMPLATE_FILE" \
        --parameters \
            ParameterKey=Environment,ParameterValue="$ENVIRONMENT" \
            ParameterKey=MatchStartupsLambdaArn,ParameterValue="$MATCH_LAMBDA_ARN" \
            ParameterKey=SendEmailLambdaArn,ParameterValue="$EMAIL_LAMBDA_ARN" \
        --capabilities CAPABILITY_IAM \
        --region "$REGION" \
        --no-cli-pager
    
    echo -e "${GREEN}✅ Stack update initiated${NC}"
    echo -e "${YELLOW}⏳ Waiting for stack update to complete...${NC}"
    
    aws cloudformation wait stack-update-complete \
        --stack-name "$STACK_NAME" \
        --region "$REGION"
    
    echo -e "${GREEN}🎉 Stack updated successfully!${NC}"
    show_outputs
}

delete_stack() {
    echo -e "${RED}⚠️  WARNING: This will delete the Step Functions state machine!${NC}"
    read -p "Are you sure? (yes/no): " confirm
    
    if [ "$confirm" != "yes" ]; then
        echo "Deletion cancelled"
        exit 0
    fi
    
    if ! check_stack_exists; then
        echo -e "${RED}❌ Stack $STACK_NAME does not exist!${NC}"
        exit 1
    fi
    
    echo -e "${YELLOW}🗑️  Deleting stack...${NC}"
    
    aws cloudformation delete-stack \
        --stack-name "$STACK_NAME" \
        --region "$REGION"
    
    echo -e "${YELLOW}⏳ Waiting for stack deletion...${NC}"
    
    aws cloudformation wait stack-delete-complete \
        --stack-name "$STACK_NAME" \
        --region "$REGION"
    
    echo -e "${GREEN}✅ Stack deleted successfully${NC}"
}

show_status() {
    if ! check_stack_exists; then
        echo -e "${RED}❌ Stack $STACK_NAME does not exist${NC}"
        exit 1
    fi
    
    echo -e "${YELLOW}📊 Stack Status:${NC}"
    aws cloudformation describe-stacks \
        --stack-name "$STACK_NAME" \
        --region "$REGION" \
        --query 'Stacks[0].{Status:StackStatus,LastUpdate:LastUpdatedTime}' \
        --output table
}

show_outputs() {
    if ! check_stack_exists; then
        return
    fi
    
    echo ""
    echo -e "${YELLOW}📋 Stack Outputs:${NC}"
    aws cloudformation describe-stacks \
        --stack-name "$STACK_NAME" \
        --region "$REGION" \
        --query 'Stacks[0].Outputs' \
        --output table
    
    echo ""
    echo -e "${GREEN}💡 State Machine ARN (use this in Lambda environment variables):${NC}"
    aws cloudformation describe-stacks \
        --stack-name "$STACK_NAME" \
        --region "$REGION" \
        --query 'Stacks[0].Outputs[?OutputKey==`StateMachineArn`].OutputValue' \
        --output text
}

case "$ACTION" in
    create)
        create_stack
        ;;
    update)
        update_stack
        ;;
    delete)
        delete_stack
        ;;
    status)
        show_status
        ;;
    outputs)
        show_outputs
        ;;
    *)
        echo -e "${RED}❌ Unknown action: $ACTION${NC}"
        echo ""
        echo "Usage: $0 [action] [options]"
        echo ""
        echo "Actions:"
        echo "  create   - Create new stack (auto-detects Lambda ARNs)"
        echo "  update   - Update existing stack"
        echo "  delete   - Delete stack"
        echo "  status   - Show stack status (default)"
        echo "  outputs  - Show stack outputs"
        echo ""
        echo "Options:"
        echo "  --match-lambda-arn ARN  - ARN of startup-matcher Lambda"
        echo "  --email-lambda-arn ARN  - ARN of send-email-notif Lambda"
        echo ""
        echo "Examples:"
        echo "  $0 create                                    # Auto-detect Lambda ARNs"
        echo "  $0 create --match-lambda-arn arn:...        # Specify ARNs"
        echo "  $0 update"
        exit 1
        ;;
esac

