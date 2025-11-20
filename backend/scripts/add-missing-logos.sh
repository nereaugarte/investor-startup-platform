#!/bin/bash

# Script to add missing logo URLs to startups in DynamoDB
# Uses Clearbit Logo API to generate logo URLs from website domains

TABLE_NAME="startup-investor-platform-dev-startups"
REGION="eu-north-1"

echo "=========================================="
echo "🎨 Adding Missing Logo URLs to Startups"
echo "=========================================="
echo ""

# Get all startups
echo "Fetching startups from DynamoDB..."
aws dynamodb scan \
  --table-name $TABLE_NAME \
  --region $REGION \
  --output json > all_startups.json

STARTUP_COUNT=$(cat all_startups.json | jq '.Items | length')
echo "Found $STARTUP_COUNT startups"
echo ""

UPDATED_COUNT=0
SKIPPED_COUNT=0

# Process each startup
cat all_startups.json | jq -c '.Items[]' | while read -r item; do
  STARTUP_ID=$(echo "$item" | jq -r '.startup_id.S')
  NAME=$(echo "$item" | jq -r '.name.S // ""')
  WEBSITE=$(echo "$item" | jq -r '.website.S // ""')
  LOGO_URL=$(echo "$item" | jq -r '.logo_url.S // ""')
  
  # Skip if already has logo
  if [ ! -z "$LOGO_URL" ] && [ "$LOGO_URL" != "null" ]; then
    echo "✅ $NAME - Already has logo: $LOGO_URL"
    ((SKIPPED_COUNT++))
    continue
  fi
  
  # Skip if no website
  if [ -z "$WEBSITE" ] || [ "$WEBSITE" == "null" ]; then
    echo "⚠️  $NAME - No website, skipping"
    ((SKIPPED_COUNT++))
    continue
  fi
  
  # Extract domain from website
  DOMAIN=$(echo "$WEBSITE" | sed -E 's|^https?://||' | sed -E 's|^www\.||' | cut -d'/' -f1 | tr '[:upper:]' '[:lower:]')
  
  if [ -z "$DOMAIN" ]; then
    echo "⚠️  $NAME - Could not extract domain from: $WEBSITE"
    ((SKIPPED_COUNT++))
    continue
  fi
  
  # Generate Clearbit logo URL
  CLEARBIT_LOGO="https://logo.clearbit.com/$DOMAIN"
  
  echo "🔄 $NAME - Adding logo: $CLEARBIT_LOGO"
  
  # Update DynamoDB item
  aws dynamodb update-item \
    --table-name $TABLE_NAME \
    --region $REGION \
    --key "{\"startup_id\": {\"S\": \"$STARTUP_ID\"}}" \
    --update-expression "SET logo_url = :logo" \
    --expression-attribute-values "{\":logo\": {\"S\": \"$CLEARBIT_LOGO\"}}" \
    --no-cli-pager > /dev/null 2>&1
  
  if [ $? -eq 0 ]; then
    echo "   ✅ Updated successfully"
    ((UPDATED_COUNT++))
  else
    echo "   ❌ Failed to update"
  fi
  
  echo ""
done

# Cleanup
rm -f all_startups.json

echo "=========================================="
echo "✨ Summary:"
echo "   Updated: $UPDATED_COUNT startups"
echo "   Skipped: $SKIPPED_COUNT startups"
echo "=========================================="

