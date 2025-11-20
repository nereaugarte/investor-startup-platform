# API Handler Lambda

Handles all REST API requests from API Gateway.

## Runtime
Python 3.11

## Endpoints
- GET /startups
- POST /preferences
- GET /preferences/{id}
- POST /bookmarks
- GET /bookmarks/{userId}
- DELETE /bookmarks/{userId}/{startupId}

## IAM Permissions
- dynamodb:GetItem
- dynamodb:PutItem
- dynamodb:Query
- dynamodb:Scan
- dynamodb:DeleteItem
