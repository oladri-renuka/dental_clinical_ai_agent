"""Simplified FastAPI app for Vonage integration."""

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

app = FastAPI(title="Dental Clinic AI Agent")

@app.get("/health")
async def health():
    """Health check endpoint."""
    return {"status": "ok", "message": "Dental Clinic AI Agent is running"}

@app.post("/incoming-call")
async def incoming_call(request: Request):
    """Handle incoming Vonage voice call."""
    return JSONResponse([{
        "action": "talk",
        "text": "Hello, thank you for calling Bright Smile Dental Clinic. How can I help you today?",
        "voiceName": "Amy",
    }])

@app.post("/vonage-speech-input")
async def vonage_speech_input(request: Request):
    """Handle user speech input from Vonage."""
    return JSONResponse([{
        "action": "talk",
        "text": "Thank you for calling. This is a test response.",
        "voiceName": "Amy",
    }])

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
