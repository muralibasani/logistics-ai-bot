"""
FastAPI server for the Logistics AI Bot chat interface.
Exposes REST API endpoints for the React frontend.
"""
import logging
import threading
import time
from contextlib import asynccontextmanager
from typing import Optional
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from dotenv import load_dotenv

from src.responder import Responder
from main import Gateway

load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Global instances
gateway: Optional[Gateway] = None
responder: Optional[Responder] = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup and shutdown events for FastAPI."""
    global gateway, responder
    
    # Startup
    logger.info("Starting Logistics AI Bot API server...")
    
    # Initialize Gateway and Responder
    gateway = Gateway()
    responder = Responder()
    
    # Start Responder consumer in background (consumes from commands topic)
    logger.info("Starting Responder service in background...")
    responder.start_consumer(background=True)
    
    # Start Gateway consumer in background (consumes from output topic)
    logger.info("Starting Gateway consumer in background...")
    gateway.start_consumer()
    
    # Give consumers time to connect
    time.sleep(2)
    
    logger.info("✅ All services started! API server ready.")
    
    yield
    
    # Shutdown
    logger.info("Shutting down services...")
    if responder:
        responder.close()
    if gateway:
        gateway.close()
    logger.info("Shutdown complete")


# Create FastAPI app
app = FastAPI(
    title="Logistics AI Bot API",
    description="REST API for the Logistics AI Bot chat interface",
    version="1.0.0",
    lifespan=lifespan
)

# Configure CORS for React frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000", "http://127.0.0.1:5173"],  # Vite default port
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Request/Response models
class ChatRequest(BaseModel):
    question: str


class ChatResponse(BaseModel):
    answer: str


@app.get("/")
async def root():
    """Health check endpoint."""
    return {"status": "ok", "message": "Logistics AI Bot API is running"}


@app.get("/health")
async def health():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "gateway": gateway is not None,
        "responder": responder is not None
    }


@app.post("/ask", response_model=ChatResponse)
async def ask_question(request: ChatRequest):
    """
    Process a user question and return the AI assistant's response.
    
    Args:
        request: Chat request containing the user's question
        
    Returns:
        Chat response containing the assistant's answer
    """
    if not gateway:
        raise HTTPException(status_code=503, detail="Gateway service not initialized")
    
    if not request.question or not request.question.strip():
        raise HTTPException(status_code=400, detail="Question cannot be empty")
    
    try:
        user_message = request.question.strip()
        logger.info(f"Received question: {user_message}")
        
        # Process message through Gateway
        message_id = gateway.process_message(user_message)
        
        if not message_id:
            raise HTTPException(status_code=500, detail="Failed to process message")
        
        # Check if response is already available (default tool handled directly)
        if message_id in gateway.pending_responses:
            response = gateway.pending_responses.pop(message_id)
            logger.info(f"Returning immediate response for message_id: {message_id}")
            return ChatResponse(answer=response)
        
        # Order tool - wait for Kafka response
        logger.info(f"Waiting for Kafka response for message_id: {message_id}")
        response = gateway.wait_for_response(message_id, timeout=30.0)
        
        if response:
            logger.info(f"Received response for message_id: {message_id}")
            return ChatResponse(answer=response)
        else:
            logger.warning(f"Timeout waiting for response to message_id: {message_id}")
            raise HTTPException(
                status_code=504,
                detail="Request timeout - the service may be processing your request. Please try again."
            )
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error processing question: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, log_level="info")

