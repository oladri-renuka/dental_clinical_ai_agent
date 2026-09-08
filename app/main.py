import logging
import uuid
import json
from datetime import datetime
from typing import Dict, Any
from contextlib import asynccontextmanager
import os
import httpx

from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import HTMLResponse, JSONResponse
from sqlalchemy.orm import Session

from config.settings import settings
from app.models.database import init_db, get_db, ConversationLog, SessionLocal
from app.models.state import ConversationState
from app.state_machine import state_machine
from app.services.session_manager import session_manager
from app.services.llm_service import LLMService
from app.services.whisper_service import WhisperService
from app.services.elevenlabs_service import ElevenLabsService
from app.services.sms_rating_service import SMSRatingService
from app.services.vonage_service import vonage_service
from dashboard.routes import get_dashboard_html

# Configure logging
logging.basicConfig(
    level=getattr(logging, settings.LOG_LEVEL),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

# Initialize services
llm_service = LLMService()
whisper_service = WhisperService()
elevenlabs_service = ElevenLabsService()
sms_rating_service = SMSRatingService()

# Vonage configuration
vonage_api_key = os.getenv("VONAGE_API_KEY")
vonage_api_secret = os.getenv("VONAGE_API_SECRET")
vonage_phone_number = os.getenv("VONAGE_PHONE_NUMBER")

if vonage_api_key and vonage_api_secret and vonage_phone_number:
    logger.info(f"✅ Vonage configured with number {vonage_phone_number}")
else:
    logger.warning("⚠️ Vonage credentials not fully set - voice calls will fail")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan context manager for startup and shutdown."""
    # Startup
    logger.info("🚀 Starting Dental Clinic Agent...")
    init_db()
    logger.info("✅ Database initialized")
    yield
    # Shutdown
    logger.info("👋 Shutting down...")


app = FastAPI(
    title="Dental Clinic AI Agent",
    description="Conversational AI for dental clinic customer service",
    version="1.0.0",
    lifespan=lifespan,
)


# ==================== WEBHOOK ENDPOINTS ====================


@app.post("/incoming-call")
async def incoming_call(request: Request):
    """Handle incoming Vonage voice call with NCCO response."""
    logger.info("📞 Incoming call received (Vonage)")

    try:
        # Parse Vonage webhook data (query params or JSON body)
        try:
            body = await request.json()
        except:
            body = {}

        query_params = dict(request.query_params)

        # Vonage sends: uuid, to, from, conversation_uuid
        call_id = body.get("uuid") or query_params.get("uuid") or str(uuid.uuid4())
        from_number = body.get("from") or query_params.get("from") or "Unknown"
        to_number = body.get("to") or query_params.get("to") or vonage_phone_number

        logger.info(f"  Call ID: {call_id}")
        logger.info(f"  From: {from_number}")

        # Create initial conversation state
        conversation_id = str(uuid.uuid4())
        state = ConversationState(
            conversation_id=conversation_id,
            call_id=call_id,
            phone_number=from_number,
            conversation_history=[],
            turn_count=0,
            start_time=datetime.now(),
            last_update=datetime.now(),
            intent=None,
            confidence=0.0,
            slots={},
            collected_slots={},
            missing_slots=[],
            resolved=False,
            escalated=False,
            escalation_reason=None,
            clarification_count=0,
            sentiment=None,
            consecutive_negative_sentiments=0,
            greeting_done=False,
            confirmation_sent=False,
        )

        # Save state to Redis
        session_manager.save_state(call_id, state)

        # Generate greeting response
        greeting_msg = "Hello, thank you for calling Bright Smile Dental Clinic. How can I help you today?"
        logger.info(f"  Greeting: {greeting_msg}")

        # Mark greeting as done
        state["conversation_history"].append({"role": "assistant", "content": greeting_msg})
        state["greeting_done"] = True
        state["turn_count"] += 1
        session_manager.save_state(call_id, state)

        # Build NCCO response (Vonage format)
        ncco = [
            {
                "action": "talk",
                "text": greeting_msg,
                "voiceName": "Amy",
            },
            {
                "action": "input",
                "type": "speech",
                "timeout": 5,
                "speechTimeout": "auto",
                "startOnSilence": 3000,
                "language": "en-US",
                "eventUrl": ["http://localhost:8000/vonage-speech-input"],  # Update for production
                "eventMethod": "POST",
            }
        ]

        logger.info("  Returning NCCO for speech gathering")
        return JSONResponse(content=ncco)

    except Exception as e:
        logger.error(f"❌ Error handling incoming call: {e}")
        ncco = [
            {
                "action": "talk",
                "text": "Sorry, there was an error. Please try again later.",
                "voiceName": "Amy",
            }
        ]
        return JSONResponse(content=ncco)


@app.post("/vonage-speech-input")
async def vonage_speech_input(request: Request):
    """Handle user speech input from Vonage."""
    logger.info("🎤 Handling user speech input (Vonage)")

    try:
        body = await request.json()

        # Vonage sends: uuid (call ID), speech (recognized text)
        call_id = body.get("uuid")
        speech_result = body.get("speech", {}).get("results", [{}])[0].get("text", "")

        logger.info(f"  Call ID: {call_id}")
        logger.info(f"  User said: {speech_result}")

        # Load current state
        state = session_manager.load_state(call_id)
        if not state:
            logger.warning(f"⚠️ No state found for call {call_id}")
            ncco = [
                {
                    "action": "talk",
                    "text": "I lost track of our conversation. Please call back.",
                    "voiceName": "Amy",
                }
            ]
            return JSONResponse(content=ncco)

        # Add user message to history
        state["conversation_history"].append({
            "role": "user",
            "content": speech_result,
        })
        state["turn_count"] += 1

        # Run through state machine
        result_state = state_machine.graph.invoke(state, config={"recursion_limit": 500})

        # Save updated state
        session_manager.save_state(call_id, result_state)

        # Get latest assistant message
        assistant_msg = ""
        if result_state["conversation_history"]:
            last_msg = result_state["conversation_history"][-1]
            if last_msg["role"] == "assistant":
                assistant_msg = last_msg["content"]

        logger.info(f"  Agent response: {assistant_msg[:80]}")

        # Build NCCO response
        ncco = [
            {
                "action": "talk",
                "text": assistant_msg,
                "voiceName": "Amy",
            }
        ]

        # If not resolved/escalated, gather more input
        if not result_state["resolved"] and not result_state["escalated"]:
            ncco.append({
                "action": "input",
                "type": "speech",
                "timeout": 5,
                "speechTimeout": "auto",
                "startOnSilence": 3000,
                "language": "en-US",
                "eventUrl": ["http://localhost:8000/vonage-speech-input"],
                "eventMethod": "POST",
            })
        else:
            # Call is complete - end the call
            logger.info(f"  Call complete: Resolved={result_state['resolved']}, Escalated={result_state['escalated']}")
            _log_conversation(call_id, result_state)

        return JSONResponse(content=ncco)

    except Exception as e:
        logger.error(f"❌ Error handling input: {e}")
        ncco = [
            {
                "action": "talk",
                "text": "Sorry, there was an error processing your request.",
                "voiceName": "Amy",
            }
        ]
        return JSONResponse(content=ncco)


@app.post("/handle-call-input")
async def handle_call_input(request: Request):
    """Deprecated: Legacy Twilio endpoint. Use /vonage-speech-input instead."""
    logger.warning("⚠️ /handle-call-input is deprecated, migrate to Vonage")
    # Redirect to vonage handler
    return await vonage_speech_input(request)


@app.post("/end-call")
async def end_call(request: Request):
    """Handle call completion and logging."""
    logger.info("📞 Call ended")

    try:
        form_data = await request.form()
        call_sid = form_data.get("CallSid")

        # Load final state
        state = session_manager.load_state(call_sid)
        if state:
            _log_conversation(call_sid, state)
            session_manager.delete_state(call_sid)
            logger.info(f"✅ Call {call_sid} logged and cleaned up")

        return JSONResponse({"status": "logged"})

    except Exception as e:
        logger.error(f"❌ Error logging call: {e}")
        return JSONResponse({"error": str(e)}, status_code=500)


def _log_conversation(call_sid: str, state: Dict[str, Any]):
    """Log conversation to database."""
    try:
        db = SessionLocal()
        conversation_log = ConversationLog(
            call_id=call_sid,
            phone_number=state.get("phone_number"),
            timestamp=datetime.now(),
            intent=state.get("intent"),
            turn_count=state.get("turn_count", 0),
            resolution_status="resolved" if state.get("resolved") else ("escalated" if state.get("escalated") else "failed"),
            escalation_reason=state.get("escalation_reason"),
            transcript=str(state.get("conversation_history", [])),
            duration_seconds=0,  # Would calculate from timestamps
        )
        db.add(conversation_log)
        db.commit()
        db.close()
    except Exception as e:
        logger.error(f"❌ Error logging conversation: {e}")


# ==================== DASHBOARD & METRICS ====================


@app.get("/dashboard")
async def dashboard():
    """Serve metrics dashboard."""
    try:
        db = SessionLocal()

        # Get metrics
        total_calls = db.query(ConversationLog).count()
        resolved_calls = db.query(ConversationLog).filter(
            ConversationLog.resolution_status == "resolved"
        ).count()
        escalated_calls = db.query(ConversationLog).filter(
            ConversationLog.resolution_status == "escalated"
        ).count()

        resolution_rate = (resolved_calls / total_calls * 100) if total_calls > 0 else 0
        escalation_rate = (escalated_calls / total_calls * 100) if total_calls > 0 else 0

        # Get recent calls
        recent_calls = db.query(ConversationLog).order_by(
            ConversationLog.timestamp.desc()
        ).limit(20).all()

        # Calculate average turns
        resolved = db.query(ConversationLog).filter(
            ConversationLog.resolution_status == "resolved"
        ).all()
        avg_turns = sum(c.turn_count for c in resolved) / len(resolved) if resolved else 0

        db.close()

        html = get_dashboard_html(
            total_calls=total_calls,
            resolution_rate=resolution_rate,
            escalation_rate=escalation_rate,
            avg_turns=avg_turns,
            recent_calls=recent_calls,
        )

        return HTMLResponse(html)

    except Exception as e:
        logger.error(f"❌ Error loading dashboard: {e}")
        return JSONResponse({"error": str(e)}, status_code=500)


@app.get("/api/metrics")
async def metrics_api():
    """Get metrics as JSON."""
    try:
        db = SessionLocal()

        total_calls = db.query(ConversationLog).count()
        resolved_calls = db.query(ConversationLog).filter(
            ConversationLog.resolution_status == "resolved"
        ).count()
        escalated_calls = db.query(ConversationLog).filter(
            ConversationLog.resolution_status == "escalated"
        ).count()

        resolution_rate = (resolved_calls / total_calls * 100) if total_calls > 0 else 0
        escalation_rate = (escalated_calls / total_calls * 100) if total_calls > 0 else 0

        db.close()

        return JSONResponse({
            "total_calls": total_calls,
            "resolved_calls": resolved_calls,
            "escalated_calls": escalated_calls,
            "resolution_rate": round(resolution_rate, 2),
            "escalation_rate": round(escalation_rate, 2),
        })

    except Exception as e:
        logger.error(f"❌ Error fetching metrics: {e}")
        return JSONResponse({"error": str(e)}, status_code=500)


# ==================== HEALTH CHECKS ====================


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    try:
        # Check database
        db = SessionLocal()
        db.execute("SELECT 1")
        db.close()

        # Check Redis
        redis_ok = session_manager.redis_client is not None or len(session_manager.fallback_storage) >= 0

        # Check Twilio
        twilio_ok = twilio_client is not None

        return JSONResponse({
            "status": "ok",
            "database": "connected",
            "redis": "connected" if session_manager.redis_client else "fallback",
            "twilio": "connected" if twilio_ok else "not configured",
            "whisper": "available",
            "elevenlabs": "available" if elevenlabs_service.is_available() else "not configured",
        })

    except Exception as e:
        logger.error(f"❌ Health check failed: {e}")
        return JSONResponse({"status": "error", "error": str(e)}, status_code=500)


# ==================== SATISFACTION RATING ====================


@app.get("/rate/{conversation_id}")
async def rate_conversation(conversation_id: str):
    """HTML page for rating a conversation via SMS link."""
    html = """
    <html>
    <head>
        <title>Rate Your Call - Bright Smile Dental</title>
        <style>
            body { font-family: Arial; text-align: center; padding: 50px; background: #f5f5f5; }
            .container { max-width: 400px; margin: 0 auto; background: white; padding: 30px; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }
            h1 { color: #2c3e50; }
            .stars { font-size: 50px; margin: 20px 0; letter-spacing: 10px; }
            .star { cursor: pointer; color: #ddd; transition: color 0.2s; }
            .star:hover, .star.active { color: #ffc107; }
            p { color: #666; margin-bottom: 20px; }
            button { background: #2c3e50; color: white; border: none; padding: 10px 30px; border-radius: 5px; cursor: pointer; font-size: 16px; }
            button:hover { background: #34495e; }
            .thank-you { display: none; color: #27ae60; font-size: 18px; }
        </style>
    </head>
    <body>
        <div class="container">
            <h1>How was your experience?</h1>
            <p>Rate the call from 1 to 5 stars</p>
            <div class="stars" id="stars">
                <span class="star" onclick="rate(1)">★</span>
                <span class="star" onclick="rate(2)">★</span>
                <span class="star" onclick="rate(3)">★</span>
                <span class="star" onclick="rate(4)">★</span>
                <span class="star" onclick="rate(5)">★</span>
            </div>
            <button id="btn" onclick="submit()" style="display:none;">Submit Rating</button>
            <div class="thank-you" id="thank-you">✓ Thank you for your feedback!</div>
        </div>
        <script>
            let selectedRating = 0;

            function rate(stars) {
                selectedRating = stars;
                const starElements = document.querySelectorAll('.star');
                starElements.forEach((star, idx) => {
                    if (idx < stars) star.classList.add('active');
                    else star.classList.remove('active');
                });
                document.getElementById('btn').style.display = 'block';
            }

            function submit() {
                if (selectedRating === 0) return;

                fetch('/submit-rating', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({
                        conversation_id: '%s',
                        rating: selectedRating
                    })
                }).then(() => {
                    document.getElementById('stars').style.display = 'none';
                    document.getElementById('btn').style.display = 'none';
                    document.getElementById('thank-you').style.display = 'block';
                });
            }
        </script>
    </body>
    </html>
    """ % conversation_id
    return HTMLResponse(html)


@app.post("/submit-rating")
async def submit_rating(request: Request):
    """Submit conversation rating."""
    try:
        data = await request.json()
        conversation_id = data.get("conversation_id")
        rating = data.get("rating")

        if not conversation_id or not rating or rating < 1 or rating > 5:
            return JSONResponse({"error": "Invalid rating"}, status_code=400)

        # Update conversation log with rating
        db = SessionLocal()
        log = db.query(ConversationLog).filter(
            ConversationLog.call_id == conversation_id
        ).first()

        if log:
            log.satisfaction_rating = rating
            db.commit()
            logger.info(f"✅ Rating {rating}/5 recorded for conversation {conversation_id}")
            return JSONResponse({"status": "recorded"})
        else:
            return JSONResponse({"error": "Conversation not found"}, status_code=404)

    except Exception as e:
        logger.error(f"❌ Error submitting rating: {e}")
        return JSONResponse({"error": str(e)}, status_code=500)


@app.get("/api/ratings/summary")
async def ratings_summary():
    """Get satisfaction ratings summary."""
    try:
        db = SessionLocal()

        # Get ratings stats
        all_ratings = db.query(ConversationLog).filter(
            ConversationLog.satisfaction_rating != None
        ).all()

        if not all_ratings:
            return JSONResponse({
                "average_rating": 0,
                "total_ratings": 0,
                "breakdown": {}
            })

        ratings = [r.satisfaction_rating for r in all_ratings]
        breakdown = {i: ratings.count(i) for i in range(1, 6)}
        average = sum(ratings) / len(ratings) if ratings else 0

        return JSONResponse({
            "average_rating": round(average, 2),
            "total_ratings": len(ratings),
            "breakdown": breakdown
        })
    except Exception as e:
        logger.error(f"❌ Error getting ratings: {e}")
        return JSONResponse({"error": str(e)}, status_code=500)


# ==================== ROOT ====================


@app.get("/")
async def root():
    """Root endpoint with API info."""
    return JSONResponse({
        "name": "Dental Clinic AI Agent",
        "status": "running",
        "twilio_number": twilio_phone_number or "not configured",
        "endpoints": {
            "health": "/health",
            "dashboard": "/dashboard",
            "metrics": "/api/metrics",
            "incoming_call": "/incoming-call (Twilio webhook)",
            "call_input": "/handle-call-input (Twilio webhook)",
        },
    })


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        app,
        host=settings.HOST,
        port=settings.PORT,
    )
