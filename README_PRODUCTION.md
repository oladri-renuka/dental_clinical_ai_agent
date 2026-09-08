# 🦷 Dental Clinic AI Agent - Production Ready

A production-grade conversational AI system for dental clinic customer service via Twilio voice calls.

## 🎯 Quick Start

### Live Phone Number
**Call now to test:** `+1-555-CLINIC-1` *(after deployment)*

---

## 📊 Current Metrics (Baseline)

From 50 test scenarios (10 types × 5 calls):

| Metric | Value | Target |
|--------|-------|--------|
| **Resolution Rate** | 70% (35/50) | ✅ 60% |
| **Intent Accuracy** | 86% (43/50) | ✅ 80% |
| **Escalation Rate** | 10% (5/50) | ✅ <20% |
| **Avg Turns** | 4.58 | ✅ <6 |

### Scenario Performance

| Scenario | Passing | Status |
|----------|---------|--------|
| 1. New Booking | 4/5 | ✅ 80% |
| 2. Cancellation | 5/5 | ✅ 100% |
| 3. Rescheduling | 2/5 | ⚠️ 40% |
| 4. Insurance Q | 5/5 | ✅ 100% |
| 5. Hours/Location | 5/5 | ✅ 100% |
| 6. After-Hours | 3-4/5 | ✅ 80% |
| 7. Angry Caller | 2/5 | ⚠️ 40% |
| 8. Unclear Intent | 1-2/5 | ⚠️ 20% |
| 9. Wrong Number | 5/5 | ✅ 100% |
| 10. Topic Switch | 3/5 | ✅ 60% |

---

## 🏗️ Architecture

### Components

```
┌─────────────────────────────────────────────────────────┐
│                    Twilio (Voice)                       │
│              (Incoming calls & TwiML)                   │
└─────────────┬───────────────────────────────────────────┘
              │
┌─────────────▼───────────────────────────────────────────┐
│                  FastAPI Server                         │
│  (/incoming-call, /handle-call-input, /dashboard)      │
└─────────────┬───────────────────────────────────────────┘
              │
     ┌────────┴────────────────────┬──────────────┐
     │                             │              │
┌────▼────────────┐  ┌───────────▼────┐  ┌───────▼────────┐
│ LangGraph State │  │   Whisper STT  │  │ ElevenLabs TTS │
│   Machine       │  │  (OpenAI API)  │  │  (Voice)       │
└────┬────────────┘  └────────────────┘  └────────────────┘
     │
     ├─→ Slot Filling (Structured extraction)
     ├─→ Intent Detection (Hard rules + LLM)
     ├─→ Confirmation (Repeat back & confirm)
     ├─→ Execution (Book/cancel/reschedule)
     └─→ Escalation (Transfer to human)
     │
┌────▼──────────────────────────────────────┐
│  SQLite Database                           │
│  ├─ Appointments (20 pre-populated)       │
│  ├─ Conversation Logs (with timestamps)   │
│  └─ Metrics & Analytics                   │
└──────────────────────────────────────────┘
```

### State Machine (LangGraph)

```
greeting → intent_detection → slot_filling → confirmation → execution
                ↓                ↓              ↓              ↓
           (no intent)      (clarify)      (no confirm)   (success)
                ↓                ↓              ↓              ↓
           escalation       waiting        escalation      end
```

---

## 🚀 Deployment

### Option 1: Railway (Recommended)

```bash
# 1. Install Railway CLI
npm install -g @railway/cli

# 2. Login and create project
railway login
railway init

# 3. Add environment variables
railway add .env

# 4. Deploy
railway up
```

**Cost**: $5-10/month (includes Redis + PostgreSQL)

### Option 2: Render

```bash
# 1. Push to GitHub
git push origin main

# 2. Go to https://dashboard.render.com
# 3. Create Web Service from GitHub
# 4. Add environment variables
# 5. Deploy
```

**Cost**: Free tier available (with limitations)

### Local Testing

```bash
# 1. Set up environment
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# 2. Create .env file
cp .env.example .env
# Edit .env with your credentials

# 3. Start server
python app/main.py

# 4. Access
# Dashboard: http://localhost:8000/dashboard
# Metrics API: http://localhost:8000/api/metrics
# Health: http://localhost:8000/health
```

---

## 📋 Configuration

### Required Environment Variables

```bash
# Twilio (Voice calls)
TWILIO_ACCOUNT_SID=ACxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
TWILIO_AUTH_TOKEN=your_auth_token
TWILIO_PHONE_NUMBER=+1234567890

# OpenAI (Speech-to-text via Whisper)
OPENAI_API_KEY=sk-xxxxxxx

# ElevenLabs (Natural voice - optional)
ELEVENLABS_API_KEY=xxxxxxxx

# Redis (Session storage)
REDIS_URL=redis://user:pass@host:port

# Database
DATABASE_URL=postgresql://user:pass@host/dbname
```

### Optional Configuration

```bash
# Server
HOST=0.0.0.0
PORT=8000
LOG_LEVEL=INFO

# Testing
SKIP_AFTER_HOURS_CHECK=false

# Clinic Info (customize for your business)
CLINIC_NAME=Bright Smile Dental Clinic
CLINIC_ADDRESS=123 Smile Street, Happiness City
CLINIC_PHONE=+1-555-CLINIC-1
```

---

## 🧪 Testing

### Run All 50 Test Scenarios

```bash
# With testing mode enabled
export SKIP_AFTER_HOURS_CHECK=true
python tests/test_runner.py

# Run specific scenario (1-10)
python tests/test_runner.py 1  # Booking
python tests/test_runner.py 4  # Insurance
```

### Test Individual Scenario

```bash
python << 'EOF'
import sys
sys.path.insert(0, '.')
from tests.scenarios import ALL_TEST_SCENARIOS
from tests.test_runner import run_test_scenario, TestMetrics

# Find and run one test
metrics = TestMetrics()
scenario = [s for s in ALL_TEST_SCENARIOS if "Booking" in s.scenario_name][0]
run_test_scenario(scenario, metrics)
metrics.print_summary()
EOF
```

---

## 📊 Dashboard

Access the real-time metrics dashboard:

```
https://your-deployed-url.com/dashboard
```

Shows:
- **Resolution Rate**: % of calls fully resolved without escalation
- **Escalation Rate**: % of calls transferred to human agent
- **Average Turns**: Number of conversation turns per call
- **Intent Accuracy**: % of correctly classified intents
- **Recent Calls**: Last 20 conversations with details

---

## 🔧 How It Works

### 1. Incoming Call Flow

```
Caller dials → Twilio receives call
  ↓
/incoming-call webhook triggered
  ↓
FastAPI returns TwiML (greeting + voice prompt)
  ↓
Twilio plays greeting using Twilio voice
  ↓
Caller speaks their request
  ↓
Twilio captures audio and sends to /handle-call-input
```

### 2. Processing Flow

```
Audio received (from Twilio)
  ↓
OpenAI Whisper transcribes to text
  ↓
Text added to conversation history
  ↓
LangGraph state machine processes:
  ├─ Intent detection (is this a booking? cancellation?)
  ├─ Slot filling (collect name, date, time)
  ├─ Confirmation (repeat back & confirm)
  ├─ Execution (book/cancel/reschedule in DB)
  └─ Escalation (if needed)
  ↓
Response generated by LLM
  ↓
TwiML returned to Twilio with response
  ↓
Twilio plays response using voice
  ↓
Continue to next turn or end call
```

### 3. Intent Types

| Intent | Example | Action |
|--------|---------|--------|
| `book_appointment` | "I want to schedule" | Collect date/time/reason |
| `cancel_appointment` | "I want to cancel" | Find & cancel appointment |
| `reschedule` | "Move my appointment" | Find old date & new date |
| `insurance_question` | "Do you accept Blue Cross?" | Answer insurance question |
| `hours_location` | "What are your hours?" | Provide clinic hours/location |
| `escalate_human` | "Talk to a person" | Transfer to human agent |
| `wrong_number` | "Is this Pizza Hut?" | Politely notify wrong number |
| `unknown` | Unclear request | Ask clarifying question |

---

## 🎤 Voice Settings

### Text-to-Speech Options

**Option 1: Twilio Built-in (Default)**
- No additional cost
- Voices: woman, man, alice
- Change in `main.py`: `response.say(..., voice="woman")`

**Option 2: ElevenLabs (Premium)**
- Natural, emotional voices
- Set `ELEVENLABS_API_KEY` in `.env`
- Costs: ~$0.30/1000 characters

**Option 3: Google Cloud Text-to-Speech**
- High-quality synthesis
- Implement in `elevenlabs_service.py`

---

## 🐛 Troubleshooting

### Common Issues

**Issue**: "No state found for call"
```
→ Redis connection failed
→ Check REDIS_URL is correct and Redis is running
→ Try restarting the service
```

**Issue**: "Twilio credentials not set"
```
→ Environment variables not loaded
→ In deployment: verify Variables tab
→ Restart service after changing env vars
```

**Issue**: "Speech not transcribed"
```
→ OpenAI API key invalid or quota exceeded
→ Check https://platform.openai.com/account/usage
→ Verify API key has billing enabled
```

**Issue**: "Call hangs up immediately"
```
→ Twilio webhook URL incorrect
→ Webhook method should be POST, not GET
→ Check firewall/CORS isn't blocking Twilio
```

### Debug Logging

Enable verbose logging:

```bash
# In .env:
LOG_LEVEL=DEBUG

# Then check logs:
# Railway: railway logs
# Render: Dashboard → Logs
# Local: stdout
```

---

## 📈 Performance Tuning

### Improve Resolution Rate

1. **Add more training data**
   - Add new test scenarios in `tests/scenarios.py`
   - Run tests to identify failure patterns

2. **Improve slot extraction**
   - Customize regex patterns in `app/services/slot_extractor.py`
   - Add domain-specific terms

3. **Tune LLM prompts**
   - Edit prompts in `app/services/llm_service.py`
   - Make more specific to dental domain

4. **Add business rules**
   - Implement hard rules for common patterns
   - Use LLM only for ambiguous cases

### Reduce Escalation Rate

1. **Better intent detection**
   - Increase hard rule coverage
   - Train LLM with dental domain examples

2. **Improve error handling**
   - Ask clarifying questions instead of escalating
   - Provide suggestions to user

3. **Context injection**
   - Include conversation history in prompts
   - Reference what was already collected

---

## 🔐 Security Considerations

### Production Checklist

- [ ] Environment variables NOT in git
- [ ] HTTPS only (Twilio requires it)
- [ ] Rate limiting on API endpoints
- [ ] Input validation on all user inputs
- [ ] Sanitize database queries (ORM handles this)
- [ ] Audit logging for sensitive actions
- [ ] Regular backups of conversation database
- [ ] GDPR/privacy compliance for call logs
- [ ] PCI-DSS if handling payment info

### Data Privacy

Conversation logs contain:
- Phone number
- Full conversation transcript
- Personal health information (dental)

**Recommendation**: Implement data retention policy
```python
# Delete conversations older than 90 days
DELETE FROM conversation_logs WHERE timestamp < NOW() - INTERVAL '90 days'
```

---

## 📞 Support & Troubleshooting

### Documentation Links

- **Twilio**: https://www.twilio.com/docs/voice
- **OpenAI Whisper**: https://platform.openai.com/docs/api-reference/audio
- **ElevenLabs**: https://elevenlabs.io/docs
- **LangGraph**: https://langchain-ai.github.io/langgraph/
- **FastAPI**: https://fastapi.tiangolo.com
- **Railway**: https://docs.railway.app

### Getting Help

1. Check logs: `railway logs`
2. Test health: `curl https://your-url.com/health`
3. View metrics: `https://your-url.com/dashboard`
4. Check database: `sqlite3 conversations.db ".tables"`

---

## 📝 Deployment Summary

### Before Going Live

1. ✅ Purchase Twilio phone number
2. ✅ Set all environment variables
3. ✅ Deploy to Railway or Render
4. ✅ Update Twilio webhook URL
5. ✅ Test health check: `/health`
6. ✅ Make test call to verify
7. ✅ Monitor dashboard: `/dashboard`
8. ✅ Set up error alerts

### After Going Live

1. Monitor metrics daily
2. Review failed calls to improve
3. Set up automated backups
4. Rotate API keys quarterly
5. Update dependencies monthly
6. Add new test scenarios as needed

---

## 📜 License

MIT License - See LICENSE file

---

**Last Updated**: September 2024  
**Version**: 1.0.0 (Production Ready)  
**Support**: See DEPLOYMENT.md for detailed setup instructions
