#!/bin/bash

# Deployment script for Lambda functions
# Usage: ./deploy-lambdas.sh [function-name]
# Example: ./deploy-lambdas.sh api-handler
# Example: ./deploy-lambdas.sh (deploys all functions)

set -e

REGION="eu-north-1"
ENVIRONMENT="dev"

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

# Lambda functions configuration
declare -A LAMBDA_FUNCTIONS=(
    ["api-handler"]="startup-investor-platform-${ENVIRONMENT}-api-handler"
    ["startup-matcher"]="startup-investor-platform-${ENVIRONMENT}-startup-matcher"
    ["send-email-notif"]="startup-investor-platform-${ENVIRONMENT}-send-email-notif"
    ["trigger-workflow"]="startup-investor-platform-${ENVIRONMENT}-trigger-workflow"
    ["batch-processor"]="startup-investor-platform-${ENVIRONMENT}-batch-processor"
)

# Check if AWS CLI is installed
if ! command -v aws &> /dev/null; then
    echo -e "${RED}❌ AWS CLI is not installed. Please install it first.${NC}"
    exit 1
fi

# Get the function to deploy (or all)
FUNCTION_TO_DEPLOY=${1:-"all"}

deploy_function() {
    local function_dir=$1
    local function_name=$2
    local aws_function_name=$3
    
    echo -e "\n${YELLOW}📦 Deploying ${function_name}...${NC}"
    
    if [ ! -d "lambda-functions/${function_dir}" ]; then
        echo -e "${RED}❌ Directory lambda-functions/${function_dir} not found${NC}"
        return 1
    fi
    
    cd "lambda-functions/${function_dir}"
    
    # Check if function exists
    if ! aws lambda get-function --function-name "$aws_function_name" --region "$REGION" &> /dev/null; then
        echo -e "${RED}❌ Lambda function ${aws_function_name} not found in AWS${NC}"
        echo -e "${YELLOW}💡 You may need to create it first via CloudFormation${NC}"
        cd ../..
        return 1
    fi
    
    # Create deployment package
    echo "Creating deployment package..."
    
    # If there's a requirements.txt, install dependencies
    if [ -f "requirements.txt" ]; then
        echo "Installing Python dependencies..."
        pip install -r requirements.txt -t . --quiet
    fi
    
    # Create zip file (exclude hidden files and common dirs)
    zip_file="${function_name}-deployment.zip"
    zip -r "$zip_file" . -x "*.git*" "*.pyc" "__pycache__/*" "*.zip" "*.md" "README*" > /dev/null 2>&1
    
    if [ ! -f "$zip_file" ]; then
        echo -e "${RED}❌ Failed to create deployment package${NC}"
        cd ../..
        return 1
    fi
    
    # Get file size
    file_size=$(du -h "$zip_file" | cut -f1)
    echo "Package size: $file_size"
    
    # Update Lambda function code
    echo "Uploading to AWS Lambda..."
    aws lambda update-function-code \
        --function-name "$aws_function_name" \
        --zip-file "fileb://${zip_file}" \
        --region "$REGION" \
        --no-cli-pager
    
    if [ $? -eq 0 ]; then
        echo -e "${GREEN}✅ ${function_name} deployed successfully${NC}"
        
        # Clean up
        rm -f "$zip_file"
        if [ -d "__pycache__" ]; then
            rm -rf __pycache__
        fi
        if [ -d "*.dist-info" ]; then
            rm -rf *.dist-info
        fi
    else
        echo -e "${RED}❌ Failed to deploy ${function_name}${NC}"
        cd ../..
        return 1
    fi
    
    cd ../..
    return 0
}

# Main deployment logic
echo -e "${GREEN}🚀 Lambda Function Deployment${NC}"
echo -e "Region: ${REGION}"
echo -e "Environment: ${ENVIRONMENT}"
echo ""

if [ "$FUNCTION_TO_DEPLOY" == "all" ]; then
    echo "Deploying all Lambda functions..."
    echo ""
    
    for func_dir in "${!LAMBDA_FUNCTIONS[@]}"; do
        aws_func_name="${LAMBDA_FUNCTIONS[$func_dir]}"
        deploy_function "$func_dir" "$func_dir" "$aws_func_name"
    done
else
    # Deploy specific function
    if [ -z "${LAMBDA_FUNCTIONS[$FUNCTION_TO_DEPLOY]}" ]; then
        echo -e "${RED}❌ Unknown function: ${FUNCTION_TO_DEPLOY}${NC}"
        echo ""
        echo "Available functions:"
        for func in "${!LAMBDA_FUNCTIONS[@]}"; do
            echo "  - $func"
        done
        exit 1
    fi
    
    aws_func_name="${LAMBDA_FUNCTIONS[$FUNCTION_TO_DEPLOY]}"
    deploy_function "$FUNCTION_TO_DEPLOY" "$FUNCTION_TO_DEPLOY" "$aws_func_name"
fi

echo ""
echo -e "${GREEN}🎉 Deployment complete!${NC}"

