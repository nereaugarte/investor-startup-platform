# 📧 SES Production Access Setup

## Current Status

**You're in SES Sandbox Mode** ⚠️

This means:
- ✅ **Can send to**: Only verified email addresses
- ❌ **Cannot send to**: Unverified email addresses (will get error)
- 📊 **Limits**: 
  - 200 emails per 24 hours
  - 1 email per second
  - Only verified recipients

## The Problem

Currently, only **your verified email** (`nerea.ugarte@alumni.esade.edu`) can receive emails. Any new user who signs up will **NOT** receive emails unless their email is verified in SES.

## Solution: Request Production Access

To allow **any user** to receive emails, you need to request **SES Production Access**.

---

## 🚀 How to Request Production Access

### Step 1: Request via AWS Console

1. Go to **AWS SES Console**: https://console.aws.amazon.com/ses/
2. Select **eu-north-1** region (top right)
3. Click **Account dashboard** (left sidebar)
4. Click **Request production access** button
5. Fill out the form:
   - **Mail Type**: Transactional
   - **Website URL**: Your app URL (https://d256cx1xju5rcz.cloudfront.net)
   - **Use case description**: 
     ```
     Startup Investor Platform - Sending personalized startup recommendations 
     to registered investors. Users opt-in to receive recommendations via 
     email when they request matches.
     ```
   - **Expected sending volume**: Start with 1,000-5,000 emails/month
   - **Compliance**: Check "I have read and agree to the AWS Service Terms"
6. Click **Submit**

### Step 2: Wait for Approval

- **Typical approval time**: 24-48 hours
- AWS will review your request
- You'll receive an email when approved

### Step 3: Verify Approval

Once approved, check your limits:
```bash
aws ses get-send-quota --region eu-north-1
```

You should see:
- `Max24HourSend`: 50,000+ (instead of 200)
- `MaxSendRate`: 14+ (instead of 1)

---

## 📋 Alternative: Verify Individual Emails (Sandbox Mode)

If you want to test with specific users while waiting for production access:

### Verify an Email Address

```bash
aws ses verify-email-identity \
  --email-address user@example.com \
  --region eu-north-1
```

The user will receive a verification email. They must click the link to verify.

### Verify a Domain (Better for Production)

If you own a domain, you can verify the entire domain:

```bash
aws ses verify-domain-identity \
  --domain example.com \
  --region eu-north-1
```

This allows sending to **any email** at that domain (e.g., `user@example.com`, `admin@example.com`).

---

## 🔍 Check Current Status

### Check if in Sandbox Mode

```bash
aws ses get-send-quota --region eu-north-1
```

**Sandbox indicators**:
- `Max24HourSend`: 200
- `MaxSendRate`: 1.0

**Production indicators**:
- `Max24HourSend`: 50,000+
- `MaxSendRate`: 14+

### Check Verified Identities

```bash
aws sesv2 list-email-identities \
  --region eu-north-1 \
  --query 'EmailIdentities[?VerificationStatus==`SUCCESS`]'
```

---

## ⚠️ Important Notes

### Sandbox Mode Limitations

- **Only verified recipients** can receive emails
- **200 emails/day limit**
- **1 email/second rate limit**
- New users will get errors: `Email address is not verified`

### Production Mode Benefits

- ✅ **Send to any email address**
- ✅ **Higher limits** (50,000+ emails/day)
- ✅ **Higher rate** (14+ emails/second)
- ✅ **No recipient verification needed**

### Best Practices

1. **Request production access** for real users
2. **Use verified domain** for better deliverability
3. **Monitor bounce/complaint rates** (keep below 5%)
4. **Set up bounce/complaint handling** (SNS topics)

---

## 🛠️ After Production Access is Approved

Once approved, **no code changes needed**! Your Lambda functions will automatically:
- Send to any email address
- Use higher rate limits
- Work for all new users

---

## 📊 Current Configuration

**Sender Email**: `nerea.ugarte@alumni.esade.edu` ✅ Verified

**Lambda Functions Using SES**:
- `startup-investor-platform-dev-startup-matcher`
- `startup-investor-platform-dev-send-email-notif`

**Region**: `eu-north-1`

---

## 🚨 Quick Fix for Testing

If you need to test with specific users right now:

1. **Verify their email**:
   ```bash
   aws ses verify-email-identity \
     --email-address testuser@example.com \
     --region eu-north-1
   ```

2. **They receive verification email** - must click link

3. **Then they can receive recommendations**

---

## ✅ Summary

**Current**: Sandbox mode - only verified emails work  
**Solution**: Request production access via AWS Console  
**Time**: 24-48 hours for approval  
**After approval**: All users can receive emails automatically!

**Action Required**: Go to AWS SES Console and request production access! 🚀

