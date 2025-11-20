#!/bin/bash

# Deployment script for backend infrastructure
# Usage: ./deploy-backend.sh [action]
# Actions: create, update, delete, status, outputs

set -e

STACK_NAME="startup-investor-platform-dev"
REGION="eu-north-1"
TEMPLATE_FILE="backend-infrastructure.yaml"

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

ACTION=${1:-status}

check_stack_exists() {
    aws cloudformation describe-stacks \
        --stack-name "$STACK_NAME" \
        --region "$REGION" \
        &> /dev/null
}

create_stack() {
    echo -e "${YELLOW}📦 Creating CloudFormation stack...${NC}"
    
    if check_stack_exists; then
        echo -e "${RED}❌ Stack $STACK_NAME already exists!${NC}"
        echo -e "${YELLOW}💡 Use 'update' action to update existing stack${NC}"
        exit 1
    fi
    
    aws cloudformation create-stack \
        --stack-name "$STACK_NAME" \
        --template-body file://"$TEMPLATE_FILE" \
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
    echo -e "${YELLOW}🔄 Updating CloudFormation stack...${NC}"
    
    if ! check_stack_exists; then
        echo -e "${RED}❌ Stack $STACK_NAME does not exist!${NC}"
        echo -e "${YELLOW}💡 Use 'create' action to create new stack${NC}"
        exit 1
    fi
    
    aws cloudformation update-stack \
        --stack-name "$STACK_NAME" \
        --template-body file://"$TEMPLATE_FILE" \
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
    echo -e "${RED}⚠️  WARNING: This will delete the entire backend infrastructure!${NC}"
    read -p "Are you sure you want to delete stack $STACK_NAME? (yes/no): " confirm
    
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
    
    echo -e "${YELLOW}⏳ Waiting for stack deletion to complete...${NC}"
    
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
        echo "Usage: $0 [action]"
        echo ""
        echo "Actions:"
        echo "  create   - Create new stack"
        echo "  update   - Update existing stack"
        echo "  delete   - Delete stack (DANGEROUS!)"
        echo "  status   - Show stack status (default)"
        echo "  outputs  - Show stack outputs"
        exit 1
        ;;
esac

