# SMTP Configuration Guide - Send Real Emails

This guide will help you configure the AI Platform to send real emails via SMTP.

## 🎯 Overview

The system now supports **two modes** for email sending:

1. **Mock Mode** (Default) - Simulates email sending for testing
2. **SMTP Mode** - Sends real emails via configured SMTP server

## 📋 Prerequisites

You'll need SMTP credentials from one of these providers:
- **Gmail** (recommended for personal use)
- **SendGrid** (recommended for production)
- **AWS SES** (for enterprise)
- **Outlook/Office 365**
- Any other SMTP service

## 🔧 Configuration Steps

### Option 1: Gmail (Easiest for Testing)

#### Step 1: Enable 2-Factor Authentication
1. Go to https://myaccount.google.com/security
2. Enable **2-Step Verification**

#### Step 2: Generate App Password
1. Go to https://myaccount.google.com/apppasswords
2. Select **App**: Mail
3. Select **Device**: Other (Custom name) → "AI Platform"
4. Click **Generate**
5. Copy the 16-character password (e.g., `abcd efgh ijkl mnop`)

#### Step 3: Configure Environment Variables
Edit `/path/to/your/ai_platform/.env`:

```bash
# SMTP Email Configuration (Gmail)
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=your-email@gmail.com
SMTP_PASSWORD=abcdefghijklmnop  # 16-char app password (no spaces)
SMTP_FROM_EMAIL=your-email@gmail.com
```

**Important:**
- Use the **App Password**, not your regular Gmail password
- Remove all spaces from the app password
- Replace `your-email@gmail.com` with your actual Gmail address

#### Step 4: Restart Services
```bash
docker compose restart mcp-server agent-service
```

#### Step 5: Test Email Sending
```bash
curl -X POST http://localhost:8002/agent/execute \
  -H "Content-Type: application/json" \
  -d '{"task":"send email to your-email@gmail.com with subject Test","model":"qwen2.5"}'
```

Check your Gmail inbox! ✉️

---

### Option 2: SendGrid (Recommended for Production)

#### Step 1: Sign Up
1. Go to https://sendgrid.com
2. Create free account (100 emails/day free)

#### Step 2: Create API Key
1. Go to **Settings** → **API Keys**
2. Click **Create API Key**
3. Name: "AI Platform"
4. Permissions: **Full Access** (or just Mail Send)
5. Copy the API key

#### Step 3: Configure Environment
Edit `.env`:

```bash
# SMTP Email Configuration (SendGrid)
SMTP_SERVER=smtp.sendgrid.net
SMTP_PORT=587
SMTP_USERNAME=apikey  # Literally the word "apikey"
SMTP_PASSWORD=SG.xxxxxxxxxxxxxxxxxxxx  # Your SendGrid API key
SMTP_FROM_EMAIL=your-verified-sender@yourdomain.com
```

#### Step 4: Verify Sender
1. In SendGrid, go to **Settings** → **Sender Authentication**
2. Verify your sender email address
3. Use that verified email as `SMTP_FROM_EMAIL`

#### Step 5: Restart and Test
```bash
docker compose restart mcp-server agent-service
curl -X POST http://localhost:8002/agent/execute \
  -H "Content-Type: application/json" \
  -d '{"task":"send email to recipient@example.com with subject Production Test","model":"qwen2.5"}'
```

---

### Option 3: Outlook/Office 365

Edit `.env`:

```bash
# SMTP Email Configuration (Outlook)
SMTP_SERVER=smtp-mail.outlook.com
SMTP_PORT=587
SMTP_USERNAME=your-email@outlook.com
SMTP_PASSWORD=your-outlook-password
SMTP_FROM_EMAIL=your-email@outlook.com
```

**Note:** May need to enable "Less secure app access" in Outlook settings.

---

### Option 4: AWS SES (Enterprise)

Prerequisites: AWS account with SES access

Edit `.env`:

```bash
# SMTP Email Configuration (AWS SES)
SMTP_SERVER=email-smtp.us-east-1.amazonaws.com  # Use your region
SMTP_PORT=587
SMTP_USERNAME=AKIAIOSFODNN7EXAMPLE  # SMTP credentials (not IAM)
SMTP_PASSWORD=wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY
SMTP_FROM_EMAIL=verified@yourdomain.com
```

**Important:**
- Use **SMTP credentials**, not IAM credentials
- Get SMTP creds from AWS SES Console → SMTP Settings
- Email must be verified in SES (or move out of sandbox)

---

## 🧪 Testing

### Test from Web UI
1. Open http://localhost:8501
2. Go to **🤖 Agent任務** tab
3. Select **qwen2.5** model
4. Type: `send email to yourself@gmail.com with subject Test`
5. Click **執行任務**
6. Check your inbox!

### Test from API
```bash
# Test with your real email
curl -X POST http://localhost:8002/agent/execute \
  -H "Content-Type: application/json" \
  -d '{
    "task": "send email to your-email@gmail.com",
    "model": "qwen2.5"
  }'
```

### Check Logs
```bash
# See if email was sent
docker compose logs mcp-server --tail 50 | grep -i email

# Look for these messages:
# ✅ Email sent successfully to [...]
# OR
# ⚠️ SMTP not configured - returning mock response
```

---

## 🔍 Troubleshooting

### Error: "SMTP AUTH extension not supported"
**Cause:** Wrong server or port
**Fix:** Double-check `SMTP_SERVER` and `SMTP_PORT`

### Error: "Authentication failed"
**Cause:** Wrong credentials
**Fix:**
- Gmail: Use App Password (not regular password)
- SendGrid: Username must be literally `apikey`
- Check for typos in password

### Error: "Connection refused"
**Cause:** Firewall or wrong port
**Fix:**
- Try port 465 (SSL) instead of 587 (TLS)
- Check Docker network connectivity

### Email Not Received
**Check:**
1. **Spam folder** - Check junk/spam
2. **Sender verification** - Some providers require verified senders
3. **Rate limits** - Gmail: 100/day, SendGrid Free: 100/day
4. **Logs** - Check if email actually sent:
   ```bash
   docker compose logs mcp-server --tail 20
   ```

### Mock Mode Still Active
**Symptoms:** Returns `"status": "sent (simulated)"` and `"method": "mock"`

**Fix:**
1. Check `.env` has SMTP config uncommented
2. Restart services: `docker compose restart mcp-server`
3. Verify environment loaded:
   ```bash
   docker compose exec mcp-server printenv | grep SMTP
   ```

---

## 🎉 Success!

Once configured, you'll see:

**API Response:**
```json
{
  "email_id": "EMAIL-20251016162500",
  "to": ["recipient@example.com"],
  "subject": "Your Subject",
  "status": "sent",
  "method": "smtp",  ← Real SMTP used!
  "sent_at": "2025-10-16T16:25:00.123456"
}
```

**Logs:**
```
✅ Email sent successfully to ['recipient@example.com']
```

---

## 📊 SMTP Configuration Comparison

| Provider | Free Tier | Setup Difficulty | Best For |
|----------|-----------|------------------|----------|
| **Gmail** | 100/day | ⭐ Easy | Personal testing |
| **SendGrid** | 100/day | ⭐⭐ Medium | Production apps |
| **AWS SES** | 62,000/month | ⭐⭐⭐ Hard | Enterprise |
| **Outlook** | Limited | ⭐ Easy | Office 365 users |

---

## 🔐 Security Best Practices

1. **Never commit `.env` to git**
   ```bash
   # Already in .gitignore, but verify:
   cat .gitignore | grep .env
   ```

2. **Use App Passwords** (Gmail)
   - Don't use your main password
   - Generate separate app password

3. **Rotate Credentials**
   - Change passwords every 90 days
   - Revoke unused app passwords

4. **Use Environment Variables**
   - Don't hardcode credentials in code
   - Use Docker secrets in production

5. **Monitor Usage**
   - Track sent emails
   - Set up alerts for rate limits

---

## 🆘 Still Need Help?

Check logs for detailed errors:
```bash
# MCP Server logs
docker compose logs mcp-server --tail 100 -f

# Agent Service logs
docker compose logs agent-service --tail 100 -f
```

Common log messages:
- `✅ Email sent successfully` - Success!
- `⚠️ SMTP not configured` - Check .env file
- `SMTP error: [535]` - Authentication failed
- `SMTP error: Connection refused` - Wrong server/port

---

## 📝 Example Full Configuration

Here's a complete working example using Gmail:

```bash
# .env file
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=myapp@gmail.com
SMTP_PASSWORD=abcdefghijklmnop
SMTP_FROM_EMAIL=myapp@gmail.com
```

Then:
```bash
docker compose restart mcp-server agent-service
```

Test:
```bash
curl -X POST http://localhost:8002/agent/execute \
  -H "Content-Type: application/json" \
  -d '{"task":"send email to test@example.com","model":"qwen2.5"}'
```

---

**Last Updated:** 2025-10-16
**Version:** 2.1.0
**Author:** AI Platform Team
