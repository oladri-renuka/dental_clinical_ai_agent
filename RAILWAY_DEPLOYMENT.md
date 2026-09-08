# 🚀 Railway Deployment - Dental Clinic AI Agent

Complete guide to deploy on Railway free tier (~$5/month after free credits).

## 📋 Prerequisites

1. **Railway Account**: https://railway.app (free tier available)
2. **GitHub Account**: For connecting repository
3. **Twilio Account**: https://twilio.com (free trial, $1/month for phone number)
4. **ElevenLabs Account**: https://elevenlabs.io (free tier: 10k chars/month)

## 💰 Cost Breakdown

| Service | Cost | Notes |
|---------|------|-------|
| Railway (free tier) | $5 - $10/month | After $5 free credits |
| Twilio phone number | $1/month | Optional, use Twilio trial |
| ElevenLabs | Free | 10,000 chars/month free tier |
| **Total** | **~$6-10/month** | Or free during trial |

---

## Step 1: Prepare Your Repository

```bash
# Make sure you have .gitignore setup
echo ".env" >> .gitignore
echo "*.db" >> .gitignore

# Commit all code (but not .env)
git add .
git commit -m "Ready for Railway deployment"
git push origin main
```

## Step 2: Create Railway Project

### 2a. Connect GitHub

1. Go to https://railway.app
2. Click "New Project"
3. Select "Deploy from GitHub repo"
4. Authorize Railway with GitHub
5. Select your `dom_proj` repository
6. Select `main` branch

### 2b. Add Services

Click "+ New" and add:

1. **PostgreSQL** (Database)
   - Railway auto-adds `DATABASE_URL`

2. **Redis** (Session Store)
   - Railway auto-adds `REDIS_URL`

## Step 3: Configure Environment Variables

In Railway Dashboard → Project → Variables:

```bash
# Twilio Configuration
TWILIO_ACCOUNT_SID=ACxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
TWILIO_AUTH_TOKEN=your_auth_token_here
TWILIO_PHONE_NUMBER=+1234567890

# ElevenLabs Configuration (Optional but recommended)
ELEVENLABS_API_KEY=xxxxxxxx

# FastAPI
HOST=0.0.0.0
PORT=8000
LOG_LEVEL=INFO

# Optional
SKIP_AFTER_HOURS_CHECK=false
```

Note: `DATABASE_URL` and `REDIS_URL` auto-added by Railway

## Step 4: Configure Build & Deployment

In Railway → Project → your service:

### Buildpack
- Let Railway auto-detect (Python)

### Build Command
```bash
pip install -r requirements.txt
```

### Start Command
```bash
uvicorn app.main:app --host 0.0.0.0 --port $PORT
```

### Environment
- Python Version: 3.11

## Step 5: Deploy

1. Click "Deploy" button in Railway
2. Wait for build to complete (3-5 minutes)
3. Copy the generated URL: `https://your-app.railway.app`

### View Logs
```bash
# Install Railway CLI
npm install -g @railway/cli

# Login
railway login

# Link project
railway link

# View logs
railway logs
```

## Step 6: Configure Twilio Webhook

Once deployed, update your Twilio phone number:

1. Go to Twilio Console → Phone Numbers → Your Number
2. Under "Voice Configuration":
   - Webhook URL: `https://your-app.railway.app/incoming-call`
   - Method: HTTP POST
3. Save

## Step 7: Test Your Agent

### Health Check
```bash
curl https://your-app.railway.app/health
```

Response should show all services "connected" or "available".

### View Dashboard
```
https://your-app.railway.app/dashboard
```

### Make a Test Call
Call your Twilio phone number and test:
- "I want to book an appointment"
- "Cancel my appointment"
- "What are your hours?"

### View Metrics
```bash
curl https://your-app.railway.app/api/metrics
```

---

## Troubleshooting

### 1. Build Fails

**Error**: `ModuleNotFoundError: No module named 'faster_whisper'`

**Solution**: Make sure `requirements.txt` has `faster-whisper==0.10.0`

**Re-deploy**:
```bash
git add requirements.txt
git commit -m "Fix dependencies"
git push origin main
```

### 2. Application Crashes

**View logs**:
```bash
railway logs --tail
```

**Common issues**:
- Missing environment variables → Add to Railway Variables
- Redis connection → Check REDIS_URL is correct
- Twilio credentials → Verify TWILIO_ACCOUNT_SID and TOKEN

### 3. Calls Don't Connect

**Check**:
1. Twilio webhook URL correct: `https://your-app.railway.app/incoming-call`
2. Webhook method is POST
3. Health check passes: `https://your-app.railway.app/health`

**Debug**:
- View logs: `railway logs --tail`
- Check Twilio Console → Logs for webhook errors

### 4. Speech Not Transcribed

**Issue**: Whisper service not working

**Solution**:
1. Check logs for errors
2. Ensure `faster-whisper` is installed
3. Try restarting: `railway redeploy`

**Note**: First call takes longer (Whisper model download ~140MB)

### 5. Out of Memory

**Issue**: Railway free tier has 512MB RAM

**Solution**:
- Use smaller Whisper model: Change `WhisperModel("tiny")`
- Increase Railway plan to $5+/month

---

## Production Checklist

- [ ] GitHub repository connected to Railway
- [ ] PostgreSQL and Redis added
- [ ] All environment variables configured
- [ ] Twilio webhook pointing to `/incoming-call`
- [ ] Health check passes
- [ ] Test call completes successfully
- [ ] Metrics dashboard displays data
- [ ] SMS rating link works
- [ ] Logs are readable

---

## Monitoring & Maintenance

### Daily
- Check dashboard for failed calls
- Monitor resolution rate trend

### Weekly
- Review logs for errors
- Update Whisper model if needed
- Check Twilio balance

### Monthly
- Backup conversation database
- Review satisfaction ratings
- Rotate API keys if needed
- Update dependencies

---

## Advanced: Custom Domain

To use your own domain (e.g., `clinic.example.com`):

1. Go to Railway → Project → Domain
2. Click "Add Custom Domain"
3. Enter your domain
4. Follow DNS configuration steps
5. Update Twilio webhook URL to your domain

---

## Tips & Tricks

### Speed Up Whisper (Local Testing)

Edit `app/services/whisper_service.py`:

```python
# Change from "base" to "tiny" for faster transcription
self.model = WhisperModel("tiny", device="cpu", compute_type="int8")
```

Tiny model: ~39MB (very fast, slightly lower accuracy)

### Fallback to Twilio Voice (No TTS)

Edit `app/main.py`:

```python
# Change from:
if elevenlabs_service.is_available():
# To:
if False:  # Disable ElevenLabs, use Twilio voice
```

### Monitor Whisper Downloads

First call will download model (~140MB), might take 30 seconds. Subsequent calls are instant.

---

## Cost Optimization

### Free Tier Limits
- Railway: $5 free credits/month
- ElevenLabs: 10,000 characters/month
- Twilio: Free trial credits available

### Reduce Costs
1. Use `ElevenLabs` Flash v2 (10x faster, 50% cheaper)
2. Keep calls under 10 minutes (save on Redis/DB)
3. Use `tiny` Whisper model for speed
4. Clean up old logs monthly

---

## Deployment Summary

```bash
# 1. Push code to GitHub
git push origin main

# 2. In Railway:
#    - Connect GitHub repo
#    - Add PostgreSQL
#    - Add Redis
#    - Set environment variables
#    - Deploy

# 3. Copy URL from Railway: https://your-app.railway.app

# 4. Update Twilio webhook to: https://your-app.railway.app/incoming-call

# 5. Test by calling your Twilio number

# Done! 🎉
```

---

## Next Steps

1. **Test thoroughly** with 50 test scenarios
2. **Monitor metrics** for a week
3. **Customize voice** (change agent responses)
4. **Add SMS integration** for scheduled reminders
5. **Setup alerts** for failed calls

---

**Questions?**
- Railway Docs: https://docs.railway.app
- Twilio Support: https://support.twilio.com
- ElevenLabs Docs: https://elevenlabs.io/docs
