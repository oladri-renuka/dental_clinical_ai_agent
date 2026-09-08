# 🚀 Quick Start Guide

Get the Dental Clinic AI Agent running in 5 minutes.

## Option 1: Local Development (Recommended for Testing)

### 1. Install Prerequisites
- Python 3.11+
- Redis (or use Docker)
- Your API keys ready:
  - OpenRouter API key (for Claude)
  - ElevenLabs API key (for voice)
  - OpenAI API key (for Whisper)
  - Twilio Account SID, Auth Token, Phone Number

### 2. Setup & Run

```bash
# Copy environment template
cp .env.example .env

# Edit .env with your API keys
nano .env

# Make script executable
chmod +x run_local.sh

# Start (creates venv, installs deps, initializes DB, starts server)
./run_local.sh
```

Your API is now running at: **http://localhost:8000**

Dashboard: **http://localhost:8000/dashboard**

### 3. Test Without Twilio (Optional)

Run the automated test suite (50 scenarios):

```bash
python tests/test_runner.py
```

Run a specific scenario:

```bash
python tests/test_runner.py 1  # "New Appointment Booking"
python tests/test_runner.py 7  # "Angry Caller"
```

---

## Option 2: Docker (Production-like)

### 1. Setup

```bash
cp .env.example .env

# Edit .env with your API keys
nano .env
```

### 2. Run

```bash
docker-compose up
```

This starts:
- Redis (session management)
- FastAPI app (port 8000)

Dashboard: **http://localhost:8000/dashboard**

---

## Option 3: Deploy to Railway (Production)

### 1. GitHub

```bash
git init
git add .
git commit -m "Dental clinic AI agent"
git remote add origin <your-github-repo>
git push -u origin main
```

### 2. Railway

1. Go to https://railway.app
2. Login with GitHub
3. "New Project" → "Deploy from GitHub repo"
4. Select your `dental-clinic-agent` repo
5. Railway auto-detects Dockerfile

### 3. Add Environment Variables

In Railway dashboard → Variables:
- `TWILIO_ACCOUNT_SID` = your SID
- `TWILIO_AUTH_TOKEN` = your token
- `TWILIO_PHONE_NUMBER` = your phone number
- `OPENROUTER_API_KEY` = your key
- `ELEVENLABS_API_KEY` = your key
- `OPENAI_API_KEY` = your key
- `REDIS_URL` = (Railway auto-generates)
- `DATABASE_URL` = `sqlite:///./dental_clinic.db`

Railway will auto-deploy. You'll get a URL like: `https://xxx.railway.app`

### 4. Configure Twilio

1. Twilio Console → Phone Numbers → (your number)
2. Voice Webhook:
   ```
   https://xxx.railway.app/incoming-call
   ```
3. Call Status Callback:
   ```
   https://xxx.railway.app/end-call
   ```

Done! Your phone number is now live with the AI agent.

---

## Testing the System

### Local Testing (No Real Calls)

```bash
# Run all 50 test scenarios
python tests/test_runner.py

# Output shows:
# - Table of all 50 tests
# - Resolution rate %
# - Escalation rate %
# - Average turns
# - Intent accuracy
# - Results saved to test_results.json
```

### Test Specific Scenario

```bash
python tests/test_runner.py 1  # New Appointment Booking
python tests/test_runner.py 2  # Cancellation
python tests/test_runner.py 7  # Angry Caller
# ... 1-10 scenarios
```

### Monitor Dashboard

```bash
# While server is running, open:
http://localhost:8000/dashboard
```

Auto-refreshes every 30 seconds. Shows:
- Total calls handled
- Resolution & escalation rates
- Avg conversation length
- Recent calls table

### Health Check

```bash
curl http://localhost:8000/health
```

---

## Configuration

### Clinic Hours & Info

Edit `config/clinic_config.py`:

```python
clinic.name = "Your Clinic Name"
clinic.phone_number = "+1-555-YOUR-NUM"
clinic.address = "Your address"

# Hours (24-hour format)
clinic.business_hours = {
    "Monday": ("08:00", "18:00"),
    "Saturday": ("09:00", "14:00"),
    "Sunday": None,  # Closed
}

# Appointment rules
clinic.min_advance_hours = 24      # Book 24+ hours ahead
clinic.max_appointments_per_day = 8
clinic.max_advance_days = 60       # Up to 60 days
```

### LLM Model

Edit `.env`:

```
LLM_MODEL=anthropic/claude-3-5-sonnet        # Best quality
LLM_MODEL=anthropic/claude-3-haiku           # Faster, cheaper
LLM_MODEL=gpt-3.5-turbo                      # OpenAI (if using OpenRouter)
```

### Voice

Edit `.env`:

```
ELEVENLABS_VOICE_ID=EXAVITQu4vr4xnSDxMaL   # Rachel (professional)
# Or try other IDs: Adam, Bella, Callum, etc.
```

---

## Troubleshooting

### "Connection refused" on localhost:8000

- Make sure the server is running: `./run_local.sh` or `docker-compose up`
- Check if port 8000 is in use: `lsof -i :8000`
- Try a different port: Change `PORT=8000` in `.env`

### "Redis connection failed"

Option A: Start Redis separately
```bash
redis-server
```

Option B: Use Docker
```bash
docker run -d -p 6379:6379 redis:7-alpine
```

Option C: Fallback to in-memory (check logs)
```bash
# Agent will log: "Redis unavailable, using in-memory fallback"
# Works for testing but won't persist across restarts
```

### "LLM API error"

- Check `OPENROUTER_API_KEY` is valid
- Verify you have credits at openrouter.ai
- Try `curl -H "Authorization: Bearer $OPENROUTER_API_KEY" https://openrouter.ai/api/v1/models`

### "Twilio not receiving calls"

1. Verify phone number is active in Twilio console
2. Check webhook URL is correct and publicly accessible
3. Monitor Twilio logs for errors
4. Test webhook locally with ngrok:
   ```bash
   ngrok http 8000
   # Use https://xxx.ngrok.io/incoming-call in Twilio
   ```

### "Whisper transcription is slow"

- This is normal (Whisper API takes ~1-3 seconds per call)
- Ensure `OPENAI_API_KEY` is valid
- Monitor OpenAI usage/credits

---

## What's Included

✅ **50 Automated Test Scenarios**
- 10 different call types
- 5 variations of each
- Measures resolution %, escalation %, intent accuracy

✅ **Real-Time Dashboard**
- Metrics & analytics
- Recent calls table
- Auto-refresh every 30 seconds

✅ **Production-Ready Code**
- Async FastAPI server
- State machine dialogue flow
- Error handling & logging
- Docker & deployment configs

✅ **Database**
- 20 pre-populated appointments
- Conversation logs (audit trail)
- SQLite (no external DB needed)

✅ **Full API**
- Twilio webhooks
- Metrics endpoint
- Health check

---

## Next Steps

1. ✅ Run `./run_local.sh` or `docker-compose up`
2. ✅ Test with `python tests/test_runner.py`
3. ✅ View dashboard at `http://localhost:8000/dashboard`
4. ✅ Configure Twilio (see README.md)
5. ✅ Deploy to Railway/Render
6. ✅ Make a test call to your live phone number!

---

## Support

- Logs: `docker logs dental-clinic-app` (if using Docker)
- Dashboard: http://localhost:8000/dashboard
- Tests: `python tests/test_runner.py`
- README: See [README.md](README.md) for full documentation

**Questions?** Check the logs or re-read the Architecture section in README.md.

Happy testing! 🎉
