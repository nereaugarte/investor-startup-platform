# 📋 Quick Reference Guide

## ✅ Your Infrastructure Status

### S3 Buckets - **YES, YOU'RE USING THEM!**

1. **Frontend Bucket** ✅ **ACTIVE**
   - Name: `startup-investor-platform-dev-frontend-459329362476`
   - **What it does**: Stores your React app (`index.html`, JS, CSS, images)
   - **How it's used**: CloudFront serves your app from this bucket
   - **Status**: ✅ Currently serving your live app at https://d256cx1xju5rcz.cloudfront.net

2. **Assets Bucket** ✅ **ACTIVE**
   - Name: `startup-investor-platform-dev-assets-459329362476`
   - **What it does**: Stores startup logos, thumbnails, and media files
   - **How it's used**: Lambda functions read/write startup assets here
   - **Status**: ✅ Used by your backend for storing startup images

### DynamoDB Tables - **YES, BOTH ARE IN PLACE!**

1. **Startups Table** ✅ **OPERATIONAL**
   - Name: `startup-investor-platform-dev-startups`
   - **What it stores**: All startup data (name, industry, funding stage, etc.)
   - **Status**: ✅ Fully operational with indexes for filtering

2. **Investors Table** ✅ **OPERATIONAL**
   - Name: `startup-investor-platform-dev-investors`
   - **What it stores**: Investor profiles, preferences, recommendations, bookmarks
   - **Status**: ✅ Fully operational

---

## 🗑️ Scripts to Delete (One-Time/Development)

These were used for initial setup and are no longer needed:

```bash
cd frontend
./cleanup-scripts.sh  # Interactive cleanup script
```

**Or manually delete:**
- ❌ `add-logo-urls.sh` - One-time data migration
- ❌ `add-missing-logos.sh` - One-time data migration
- ❌ `fix-logo-urls.sh` - One-time data fix
- ❌ `remove-duplicates.sh` - One-time cleanup
- ❌ `delete-all-startups.sh` - Testing only
- ❌ `add-test-investor.sh` - Testing only
- ❌ `update-thumbnail-lambda.sh` - One-time setup
- ❌ `vercel.json` - Not using Vercel (using AWS)
- ❌ `response.json` - Test data (review first)

---

## ✅ Scripts to Keep

- ✅ **`frontend/deploy.sh`** - **ESSENTIAL** - Deploys frontend to S3+CloudFront
- ✅ **`backend/deploy-lambdas.sh`** - **NEW** - Deploys Lambda functions

---

## 🆕 New Scripts Added

### 1. **`backend/deploy-lambdas.sh`** ⭐ **NEW!**

**Purpose**: Deploy your Lambda functions when you make code changes

**Usage**:
```bash
cd backend

# Deploy all Lambda functions
./deploy-lambdas.sh

# Deploy specific function
./deploy-lambdas.sh api-handler
./deploy-lambdas.sh startup-matcher
```

**What it does**:
- Packages Lambda function code
- Uploads to AWS Lambda
- Updates function code

### 2. **`frontend/cleanup-scripts.sh`** 🧹 **NEW!**

**Purpose**: Interactive script to safely delete unnecessary files

**Usage**:
```bash
cd frontend
./cleanup-scripts.sh
```

---

## 📝 What You Need to Add

### 1. **Update API Handler Lambda** ⚠️ **DO THIS NOW**

You made changes to `api-handler/index.py` (added `/match-startups` endpoint). Deploy it:

```bash
cd backend
./deploy-lambdas.sh api-handler
```

This will make your "Get Recommendations" button work with the new endpoint!

### 2. **Optional: Backup Script** (Recommended)

Create `scripts/backup-dynamodb.sh` for regular backups.

### 3. **Optional: Infrastructure Deployment Script**

Create `backend/deploy-infrastructure.sh` to update CloudFormation stacks.

---

## 🚀 Quick Commands

### Deploy Frontend
```bash
cd frontend
./deploy.sh
```

### Deploy Backend Lambda
```bash
cd backend
./deploy-lambdas.sh [function-name]
```

### Check Infrastructure
```bash
# List S3 buckets
aws s3 ls --region eu-north-1 | grep startup-investor

# List DynamoDB tables
aws dynamodb list-tables --region eu-north-1

# Check Lambda functions
aws lambda list-functions --region eu-north-1 | grep startup-investor
```

---

## 📊 Summary

| Resource | Status | Purpose |
|----------|--------|---------|
| S3 Frontend Bucket | ✅ Active | Hosts React app |
| S3 Assets Bucket | ✅ Active | Stores startup logos/images |
| DynamoDB Startups | ✅ Active | Startup data |
| DynamoDB Investors | ✅ Active | Investor profiles |
| CloudFront | ✅ Active | CDN for frontend |
| Lambda Functions | ✅ Active | Backend logic |
| API Gateway | ✅ Active | API endpoints |

**Everything is set up and working!** 🎉

---

## ⚠️ **Action Required**

**Deploy your updated API handler Lambda** to activate the `/match-startups` endpoint fix:

```bash
cd backend
./deploy-lambdas.sh api-handler
```

This will make your "Get Recommendations" button work perfectly!

