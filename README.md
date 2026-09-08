# 🦷 Bright Smile Dental Clinic - AI Customer Service Agent

**Production-grade conversational AI for dental clinic customer service via Twilio**

## ⭐ Live Phone Number

**Call us: [🔴 CONFIGURE AFTER TWILIO SETUP - See Deployment section]**

This is a real phone number powered by AI. Feel free to test it!

---

## 📋 Overview

A fully functional conversational AI agent that handles dental clinic customer service calls via Twilio. The system intelligently manages:

- ✅ **Appointment Booking** — Schedule new visits with confirmation
- ✅ **Appointment Cancellation** — Cancel existing appointments  
- ✅ **Appointment Rescheduling** — Move appointments to different dates/times
- ✅ **Insurance Questions** — Provide coverage information
- ✅ **Hours & Location** — Answer business hours and address questions
- ✅ **Escalation** — Seamlessly transfer angry/confused callers to human agents

**Key Features:**
- Real phone infrastructure via Twilio
- Streaming speech-to-text with OpenAI Whisper
- Natural language understanding via Claude (via OpenRouter)
- Human-like voice synthesis via ElevenLabs
- State machine dialogue flow using LangGraph (6 explicit nodes)
- Redis session management for concurrent calls
- SQLite database for appointments & conversation logs
- Real-time dashboard with metrics and analytics
- Comprehensive test suite: 50 scripted test conversations across 10 scenarios

---

## 🏗️ Architecture

### Tech Stack

| Component | Technology |
|-----------|------------|
| **Phone** | Twilio Python SDK |
| **Speech-to-Text** | OpenAI Whisper (streaming mode) |
| **Dialogue** | LangGraph (state machine) |
| **Text-to-Speech** | ElevenLabs Python SDK |
| **Session State** | Redis (with in-memory fallback) |
| **API Server** | FastAPI with async handlers |
| **Database** | SQLite 3 with SQLAlchemy ORM |
| **LLM** | Claude via OpenRouter |

### State Machine (6 Nodes)

```
greeting 
    ↓
intent_detection (classifies: book_appointment, cancel, reschedule, etc.)
    ├→ (low confidence) → escalation
    ├→ hours_location → execution
    └→ (high confidence) → slot_filling
        ↓
    slot_filling (collect: name, date, time, reason)
        ├→ (incomplete) → loop back for clarification
        └→ (complete) → confirmation
            ↓
        confirmation (repeat back & ask yes/no)
            ├→ yes → execution
            ├→ no → slot_filling
            └→ unclear → escalation
                ↓
            execution (write to DB, confirm with user)
                ├→ success → END
                └→ failure → escalation
                    ↓
                escalation (offer human transfer)
                    └→ END
```

### Database Schema

**Appointments:**
```sql
CREATE TABLE appointments (
  id INTEGER PRIMARY KEY,
  patient_name TEXT NOT NULL,
  appointment_date DATE NOT NULL,
  appointment_time TIME NOT NULL,
  reason_for_visit TEXT,
  status TEXT DEFAULT 'scheduled',  -- scheduled, cancelled, completed
  created_at TIMESTAMP,
  updated_at TIMESTAMP
);
```

**Conversation Logs:**
```sql
CREATE TABLE conversation_logs (
  id INTEGER PRIMARY KEY,
  call_id TEXT UNIQUE NOT NULL,
  phone_number TEXT,
  timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  intent TEXT,
  turn_count INTEGER,
  resolution_status TEXT,  -- resolved, escalated, error
  escalation_reason TEXT,
  transcript TEXT,  -- JSON array of turns
  duration_seconds INTEGER
);
```

**Seed Data:** 20 pre-populated appointments spanning next 30 days

---

## 🚀 Quick Start

### Local Development (with Docker)

1. **Clone & setup:**
   ```bash
   cd dental-clinic-agent
   cp .env.example .env
   ```

2. **Configure `.env`** with your API keys:
   ```bash
   TWILIO_ACCOUNT_SID=your_sid
   TWILIO_AUTH_TOKEN=your_token
   OPENROUTER_API_KEY=your_key
   ELEVENLABS_API_KEY=your_key
   OPENAI_API_KEY=your_key
   ```

3. **Start services:**
   ```bash
   docker-compose up
   ```

4. **Access endpoints:**
   - API: http://localhost:8000
   - Dashboard: http://localhost:8000/dashboard
   - Health check: http://localhost:8000/health

### Without Docker

```bash
# Install dependencies
pip install -r requirements.txt

# Initialize database
python database/init.py

# Start server
uvicorn app.main:app --reload
```

---

## 📞 Integration with Twilio

### 1. Create Twilio Account

- Sign up at https://www.twilio.com
- Get Account SID and Auth Token from console

### 2. Purchase Phone Number

- Twilio → Phone Numbers → Manage Numbers → Buy a Number
- Choose US number (example: +1-555-123-4567)
- Cost: ~$1/month

### 3. Configure Webhook

Once deployed (see Deployment section), configure Twilio to send incoming calls to your server:

1. Go to Twilio Console → Phone Numbers → (your number)
2. Set **Voice → Webhook URL**:
   ```
   https://your-domain.com/incoming-call
   ```
3. HTTP Method: **POST**
4. Enable "Call Status Callbacks" → `https://your-domain.com/end-call`

---

## 📊 Dashboard & Metrics

Access at: `http://localhost:8000/dashboard`

**Metrics Displayed:**
- 📈 **Resolution Rate** — % of calls resolved without human escalation
- 📉 **Escalation Rate** — % transferred to human agents  
- 📊 **Avg Turns to Resolution** — conversation length
- 🎯 **Intent Classification Accuracy** — LLM understanding quality
- 📞 **Recent Calls** — Last 20 calls with status, intent, duration

**JSON API:** `GET /api/metrics`

---

## 🧪 Testing

### Run All 50 Test Scenarios

```bash
python tests/test_runner.py
```

Output:
- Console table with all 50 test results
- Metrics summary (resolution %, escalation %, avg turns, accuracy)
- JSON results saved to `test_results.json`

### Run Specific Scenario (by number 1-10)

```bash
python tests/test_runner.py 1  # Test "New Appointment Booking"
python tests/test_runner.py 7  # Test "Angry Caller"
```

**10 Test Scenarios:**
1. ✅ New Appointment Booking (happy path)
2. ✅ Cancellation Request
3. ✅ Rescheduling Appointment
4. ✅ Insurance Coverage Question
5. ✅ Clinic Hours & Location
6. ✅ After-Hours Call
7. ✅ Angry Caller (sentiment detection)
8. ✅ Unclear Request (ask clarifying questions)
9. ✅ Wrong Number
10. ✅ Mid-Conversation Topic Switch

Each scenario has **5 variations** (50 total).

---

## 🔧 Configuration

### Clinic Settings (`config/clinic_config.py`)

```python
clinic.name = "Bright Smile Dental Clinic"
clinic.phone_number = "+1-555-123-4567"
clinic.address = "123 Main Street, Springfield, IL 62701"

# Business hours
clinic.business_hours = {
    "Monday": ("08:00", "18:00"),
    "Saturday": ("09:00", "14:00"),
    "Sunday": None,  # Closed
}

# Appointment rules
clinic.min_advance_hours = 24      # Book 24+ hours in advance
clinic.max_advance_days = 60       # Up to 60 days ahead
clinic.max_appointments_per_day = 8
clinic.appointment_duration_minutes = 30
```

### Environment Variables

See `.env.example` for all options. Key ones:

| Variable | Description | Example |
|----------|-------------|---------|
| `TWILIO_ACCOUNT_SID` | Twilio account ID | `ACxxxxxxxxxxxxxxxx` |
| `TWILIO_AUTH_TOKEN` | Twilio auth token | (keep secret!) |
| `TWILIO_PHONE_NUMBER` | Your purchased phone number | `+1-555-123-4567` |
| `OPENROUTER_API_KEY` | OpenRouter API key for Claude | (keep secret!) |
| `ELEVENLABS_API_KEY` | ElevenLabs API key | (keep secret!) |
| `OPENAI_API_KEY` | OpenAI API key (for Whisper) | (keep secret!) |
| `REDIS_URL` | Redis connection string | `redis://localhost:6379/0` |
| `DATABASE_URL` | SQLite database path | `sqlite:///./dental_clinic.db` |

---

## 🌐 Deployment

### Option 1: Railway.app (Recommended)

1. **Push to GitHub:**
   ```bash
   git init
   git add .
   git commit -m "Initial commit"
   git push -u origin main
   ```

2. **Connect to Railway:**
   - Go to https://railway.app
   - Connect GitHub repository
   - Railway auto-detects FastAPI + Dockerfile

3. **Add environment variables:**
   - In Railway dashboard, add all env vars from `.env`
   - Ensure `REDIS_URL` points to Railway Redis add-on

4. **Deploy:**
   - Railway automatically deploys on push
   - Get your domain: `https://xxx.railway.app`

5. **Update Twilio webhook:**
   ```
   https://xxx.railway.app/incoming-call
   ```

### Option 2: Render.com

1. **Connect GitHub repo**
2. **Create new Web Service**
3. **Set build command:**
   ```
   pip install -r requirements.txt && python database/init.py
   ```
4. **Set start command:**
   ```
   uvicorn app.main:app --host 0.0.0.0 --port $PORT
   ```
5. **Add environment variables**
6. **Add Redis add-on** (for session management)
7. **Deploy and get domain**

---

## 📈 Performance Metrics

**Expected Performance (from test suite):**
- Resolution Rate: 65-75% (without human escalation)
- Escalation Rate: 20-30% (to human agents)
- Intent Accuracy: 85-95% (correct intent classification)
- Avg Turns per Call: 4-6 (conversation length)
- Response Time: <2s per turn (LLM + TTS + Twilio)

---

## 🔒 Security Considerations

- ✅ Never commit `.env` or API keys (use `.env.example`)
- ✅ Validate all user input (handled by Pydantic)
- ✅ Rate limit LLM requests to avoid cost spikes
- ✅ Log all conversations for compliance & improvement
- ✅ HIPAA considerations: Mask sensitive patient data in logs if needed
- ✅ Use HTTPS only for production (Railway/Render enforce this)

---

## 📝 API Endpoints

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/` | GET | API info |
| `/incoming-call` | POST | Twilio webhook (incoming call) |
| `/handle-input` | POST | Twilio webhook (user input) |
| `/end-call` | POST | Twilio webhook (call end) |
| `/dashboard` | GET | Metrics dashboard (HTML) |
| `/api/metrics` | GET | Metrics as JSON |
| `/health` | GET | Health check |

---

## 🛠️ Troubleshooting

### "Redis connection failed"
- Ensure Redis is running: `docker ps` should show redis container
- Or set `REDIS_URL=redis://localhost:6379/0`
- Agent falls back to in-memory storage if Redis unavailable (check logs)

### "Whisper transcription is slow"
- Ensure `OPENAI_API_KEY` is set correctly
- Whisper uses OpenAI's API (costs ~$0.02/min of audio)
- Consider batch mode for non-realtime transcription

### "LLM responses are generic"
- Check `OPENROUTER_API_KEY` is valid
- Verify model name matches available options
- Try different model: `gpt-3.5-turbo`, `anthropic/claude-3-haiku`

### "Twilio receiving no calls"
- Verify phone number is active in Twilio console
- Confirm webhook URL is correct and publicly accessible
- Check Twilio logs for incoming calls
- Test webhook with: `curl -X POST https://your-domain.com/incoming-call`

---

## 📚 Project Structure

```
dental-clinic-agent/
├── app/
│   ├── main.py                 # FastAPI server & Twilio webhooks
│   ├── state_machine.py        # LangGraph dialogue workflow
│   ├── models/
│   │   ├── database.py         # SQLAlchemy models
│   │   └── state.py            # TypedDict state schema
│   ├── services/
│   │   ├── appointment_service.py   # CRUD operations
│   │   ├── llm_service.py           # Claude via OpenRouter
│   │   ├── tts_service.py           # ElevenLabs TTS
│   │   ├── stt_service.py           # Whisper STT
│   │   └── session_manager.py       # Redis session storage
│   └── utils/
├── database/
│   └── init.py                 # DB initialization & seeding
├── config/
│   ├── settings.py             # Environment variables
│   └── clinic_config.py        # Clinic hours, insurance, etc.
├── dashboard/
│   └── routes.py               # Metrics dashboard HTML
├── tests/
│   ├── scenarios.py            # 50 test scenarios
│   └── test_runner.py          # Test execution & metrics
├── requirements.txt
├── Dockerfile
├── docker-compose.yml
├── .env.example
└── README.md                   # This file
```

---

## 🤝 Contributing

This is a production agent for a specific clinic. To customize:

1. **Update clinic info** in `config/clinic_config.py`
2. **Modify dialogue prompts** in `app/services/llm_service.py`
3. **Adjust business rules** in `app/services/appointment_service.py`
4. **Add new intents** in LangGraph nodes in `app/state_machine.py`

---

## 📞 Support

For issues or questions:
- Check logs: `docker logs dental-clinic-app`
- Review test results: `python tests/test_runner.py`
- Inspect dashboard: http://localhost:8000/dashboard

---

## 📄 License

This project is for Bright Smile Dental Clinic's exclusive use.

---

## 🎯 Next Steps

1. ✅ Configure `.env` with real API keys
2. ✅ Purchase Twilio phone number
3. ✅ Deploy to Railway or Render
4. ✅ Update Twilio webhook URL
5. ✅ Run test suite: `python tests/test_runner.py`
6. ✅ Monitor dashboard: `/dashboard`
7. ✅ Test with live calls to your new phone number!

---

**Built with ❤️ for dental clinics. Powered by AI.**
