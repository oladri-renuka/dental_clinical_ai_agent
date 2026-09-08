# Deployment Guide - Dental Clinic AI Agent

## Prerequisites

1. **Twilio Account**
   - Sign up at https://www.twilio.com
   - Purchase a phone number (~$1/month)
   - Get Account SID and Auth Token from Console

2. **OpenAI Account**
   - API key for Whisper (STT)
   - Sign up at https://platform.openai.com

3. **ElevenLabs Account** (Optional but recommended)
   - API key for natural voice synthesis
   - Sign up at https://elevenlabs.io

4. **Railway or Render Account**
   - Railway: https://railway.app
   - Render: https://render.com

5. **Redis** (Cloud)
   - Option 1: Railway Redis (included)
   - Option 2: Redis Cloud (https://redis.com/cloud)
   - Option 3: Use fallback (not recommended for production)

---

## Step 1: Set Up Local Environment

```bash
# Clone repository
git clone <repo>
cd dom_proj

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Create .env file
cp .env.example .env

# Edit .env with your credentials
# TWILIO_ACCOUNT_SID=ACxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
# TWILIO_AUTH_TOKEN=your_auth_token
# TWILIO_PHONE_NUMBER=+1234567890
# OPENAI_API_KEY=sk-xxxxxxx
# ELEVENLABS_API_KEY=xxxxxxxx
# REDIS_URL=redis://localhost:6379
```

---

## Step 2: Set Up Twilio

1. **Purchase Phone Number**
   - Go to Twilio Console → Phone Numbers → Buy a Number
   - Choose a number in your country
   - Confirm purchase (~$1/month)

2. **Configure Webhook**
   - Go to Phone Number Settings
   - Under "Voice Configuration":
     - Webhook URL: `https://your-domain.com/incoming-call`
     - Method: HTTP POST
   - Save

---

## Step 3: Deploy to Railway

### 3a. Connect Repository

```bash
# Install Railway CLI
npm install -g @railway/cli

# Login to Railway
railway login

# Create new project
railway init

# Link repository
railway link

# Push code
git push
```

### 3b. Configure Environment Variables

In Railway Dashboard:
1. Go to Project → Variables
2. Add all variables from `.env`:
   - `TWILIO_ACCOUNT_SID`
   - `TWILIO_AUTH_TOKEN`
   - `TWILIO_PHONE_NUMBER`
   - `OPENAI_API_KEY`
   - `ELEVENLABS_API_KEY`
   - `REDIS_URL` (Railway auto-adds Redis plugin)
   - `DATABASE_URL` (Railway auto-adds PostgreSQL plugin)

### 3c. Add Redis and Database

1. Click "+ New"
2. Select "Redis" → Create
3. Select "PostgreSQL" → Create

Variables are automatically added.

### 3d. Deploy

```bash
# Deploy to Railway
railway up

# View logs
railway logs

# Get deployment URL
railway open
```

---

## Step 4: Deploy to Render (Alternative)

### 4a. Connect GitHub

1. Go to https://dashboard.render.com
2. Click "New +" → "Web Service"
3. Connect your GitHub repository
4. Select branch to deploy (main)

### 4b. Configure Service

1. **Name**: `dental-clinic-ai`
2. **Runtime**: Python 3.11
3. **Build Command**: `pip install -r requirements.txt`
4. **Start Command**: `uvicorn app.main:app --host 0.0.0.0 --port $PORT`
5. **Environment**: Production

### 4c. Add Environment Variables

In Render Dashboard → Environment:
```
TWILIO_ACCOUNT_SID=ACxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
TWILIO_AUTH_TOKEN=your_auth_token
TWILIO_PHONE_NUMBER=+1234567890
OPENAI_API_KEY=sk-xxxxxxx
ELEVENLABS_API_KEY=xxxxxxxx
REDIS_URL=redis://default:password@host:port
DATABASE_URL=postgresql://user:password@host/database
```

### 4d. Add Redis Database

1. Click "New +" → "Redis"
2. Name: `dental-clinic-redis`
3. Copy connection string to `REDIS_URL`

### 4e. Deploy

1. Click "Create Web Service"
2. Wait for deployment (3-5 minutes)
3. Render provides a URL: `https://dental-clinic-ai.onrender.com`

---

## Step 5: Update Twilio Webhook

Once deployed, update your Twilio phone number configuration:

**In Twilio Console → Phone Numbers → Your Number:**
- Webhook URL: `https://your-deployed-url.com/incoming-call`
- Method: HTTP POST

---

## Step 6: Test the System

### Make a Test Call

```bash
# Test health endpoint
curl https://your-deployed-url.com/health

# Test dashboard
open https://your-deployed-url.com/dashboard

# Make a test call to your Twilio number
# Your agent should answer and walk through the conversation
```

### Test Scenarios

1. **Book Appointment**
   - Call: "I need to schedule an appointment"
   - Provide: Name, date/time, reason
   - Expected: Confirmation → Appointment booked

2. **Cancel Appointment**
   - Call: "I want to cancel"
   - Provide: Name, appointment details
   - Expected: Cancellation confirmed

3. **After Hours**
   - Call outside 8 AM-6 PM Mon-Fri or 9 AM-2 PM Sat
   - Expected: Escalation to human agent

4. **Insurance Question**
   - Call: "Do you accept [insurance]?"
   - Expected: Yes/No → Provide details

---

## Troubleshooting

### "No state found for call"
- Redis connection failed
- Check `REDIS_URL` is correct
- Verify Redis is running/accessible

### "Twilio credentials not set"
- Environment variables not loaded
- In Render/Railway: Check "Environment" tab
- Restart service after updating variables

### "Speech not transcribed"
- OpenAI API key invalid
- Check quota and billing on platform.openai.com
- Test with curl:
```bash
curl -H "Authorization: Bearer $OPENAI_API_KEY" https://api.openai.com/v1/models
```

### "Call hangs up immediately"
- Twilio webhook URL incorrect
- Webhook method should be POST
- Check server logs: `railway logs` or Render logs

### Dashboard shows no calls
- Check database connection
- Verify calls are reaching `/handle-call-input` endpoint
- Check server logs for errors

---

## Monitoring

### View Metrics Dashboard
- URL: `https://your-deployed-url.com/dashboard`
- Shows: Resolution rate, escalation rate, conversation turns, intent accuracy

### View API Metrics
```bash
curl https://your-deployed-url.com/api/metrics
```

### View Logs
- **Railway**: `railway logs`
- **Render**: Dashboard → Logs tab

---

## Production Checklist

- [ ] Twilio phone number purchased
- [ ] OpenAI API key configured
- [ ] ElevenLabs API key configured (or use Twilio voice)
- [ ] Redis configured (Railway/Render/Redis Cloud)
- [ ] Database configured (PostgreSQL recommended)
- [ ] Environment variables set in deployment platform
- [ ] Twilio webhook pointing to `/incoming-call`
- [ ] Health check passes: `GET /health`
- [ ] Dashboard loads: `GET /dashboard`
- [ ] Test call completes successfully
- [ ] Metrics logged to database
- [ ] Error handling verified

---

## Next Steps

1. **Customize Voice**
   - Modify agent responses in `app/state_machine.py`
   - Change Twilio voice (woman, man, alice) in `main.py`
   - Integrate ElevenLabs for custom voice

2. **Add SMS Satisfaction Rating**
   - Send SMS after call with 1-5 rating link
   - Track satisfaction in database

3. **Implement Call Recording**
   - Enable Twilio call recording
   - Store recordings in S3
   - Add to dashboard

4. **Advanced Analytics**
   - Sentiment analysis per call
   - Common failure patterns
   - Agent performance metrics

---

## Support

- Twilio Docs: https://www.twilio.com/docs
- Railway Docs: https://docs.railway.app
- Render Docs: https://render.com/docs
- OpenAI API: https://platform.openai.com/docs
