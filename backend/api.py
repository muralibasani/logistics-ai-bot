"""
FastAPI server for the Logistics AI Bot chat interface.
Exposes REST API endpoints for the React frontend.
"""
import logging
import threading
import time
import asyncio
from contextlib import asynccontextmanager
from typing import Optional
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from dotenv import load_dotenv

from src.responder import Responder
from main import Gateway
from src.insights_service import generate_insights
from src.kafka_utils.producer import KafkaProducer
from src.kafka_utils.config import TOPICS
import uuid
from datetime import datetime

load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def publish_insights_to_kafka(insights: list) -> int:
    """
    Publish insights to Kafka topic.
    
    Args:
        insights: List of insight dictionaries
        
    Returns:
        Number of insights successfully published
    """
    global insights_producer
    
    if not insights_producer:
        logger.error("Insights producer not initialized")
        return 0
    
    if not insights_producer._connected:
        logger.warning("Insights producer not connected, attempting to connect...")
        if not insights_producer.connect():
            logger.error("Failed to connect insights producer, skipping Kafka publish")
            return 0
    
    published_count = 0
    for insight in insights:
        try:
            insight_id = str(uuid.uuid4())
            insight_event = {
                "insight_id": insight_id,
                "insight_type": insight["insight_type"],
                "title": insight["title"],
                "description": insight["description"],
                "data": insight["data"],
                "priority": insight["priority"],
                "timestamp": datetime.utcnow().isoformat()
            }
            
            logger.debug(f"Publishing insight '{insight['title']}' to topic '{TOPICS['insights']}'")
            success = insights_producer.produce(
                topic=TOPICS["insights"],
                message=insight_event,
                key=insight_id
            )
            
            if success:
                published_count += 1
                logger.debug(f"✅ Published insight '{insight['title']}' (ID: {insight_id})")
            else:
                logger.warning(f"❌ Failed to publish insight '{insight['title']}' to Kafka")
        except Exception as e:
            logger.error(f"Error publishing insight '{insight.get('title', 'unknown')}': {e}")
    
    if published_count > 0:
        insights_producer.flush(timeout=5.0)
        logger.info(f"✅ Published {published_count}/{len(insights)} insights to Kafka topic '{TOPICS['insights']}'")
    else:
        logger.warning(f"⚠️ No insights were published to Kafka (0/{len(insights)} successful)")
    
    return published_count


def run_insights_scheduler():
    """
    Background task that generates and publishes insights every hour.
    Runs in a separate thread.
    """
    global _insights_scheduler_running, insights_producer
    
    # Wait a bit before first run to let services fully start
    logger.info("⏳ Insights scheduler waiting 30 seconds before first run...")
    time.sleep(30)
    
    # Verify producer is still connected
    if not insights_producer or not insights_producer._connected:
        logger.error("❌ Insights producer not connected, scheduler cannot publish insights")
        return
    
    logger.info("🕐 Insights scheduler started - will generate insights every hour")
    
    while _insights_scheduler_running:
        try:
            logger.info("📊 Generating scheduled insights...")
            
            # Check producer connection before generating
            if not insights_producer or not insights_producer._connected:
                logger.warning("⚠️ Insights producer not connected, attempting to reconnect...")
                if insights_producer:
                    insights_producer.connect()
                if not insights_producer or not insights_producer._connected:
                    logger.error("❌ Failed to reconnect insights producer, skipping this run")
                    time.sleep(60)  # Wait 1 minute before retrying
                    continue
            
            insights = generate_insights()
            
            if insights:
                logger.info(f"📈 Generated {len(insights)} insights, publishing to Kafka...")
                published = publish_insights_to_kafka(insights)
                logger.info(f"✅ Scheduled insights generation complete: {len(insights)} insights generated, {published} published to Kafka topic '{TOPICS['insights']}'")
            else:
                logger.warning("⚠️ No insights generated in scheduled run")
                
        except Exception as e:
            logger.error(f"❌ Error in scheduled insights generation: {e}", exc_info=True)
        
        # Wait 1 hour (3600 seconds) before next run
        # Use a loop with smaller intervals to allow for graceful shutdown
        for _ in range(360):  # 360 * 10 seconds = 3600 seconds = 1 hour
            if not _insights_scheduler_running:
                break
            time.sleep(10)
    
    logger.info("🛑 Insights scheduler stopped")


# Global instances
gateway: Optional[Gateway] = None
responder: Optional[Responder] = None
insights_producer: Optional[KafkaProducer] = None
_insights_scheduler_running = False


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup and shutdown events for FastAPI."""
    global gateway, responder, insights_producer, _insights_scheduler_running
    
    # Startup
    logger.info("Starting Logistics AI Bot API server...")
    
    # Initialize Gateway and Responder
    gateway = Gateway()
    responder = Responder()
    
    # Initialize Insights Producer
    insights_producer = KafkaProducer()
    if not insights_producer.connect():
        logger.warning("Failed to connect insights producer, insights will not be published to Kafka")
    else:
        logger.info("✅ Insights producer connected successfully")
        # Start scheduled insights generation (every hour)
        _insights_scheduler_running = True
        insights_scheduler_thread = threading.Thread(
            target=run_insights_scheduler,
            daemon=True,
            name="InsightsScheduler"
        )
        insights_scheduler_thread.start()
        logger.info("✅ Insights scheduler thread started (will generate insights every hour after 30s initial delay)")
        
        # Also trigger an immediate generation for testing (optional - can be removed)
        # Uncomment the next 3 lines if you want immediate generation on startup
        # immediate_thread = threading.Thread(target=lambda: (time.sleep(5), publish_insights_to_kafka(generate_insights())), daemon=True)
        # immediate_thread.start()
        # logger.info("📊 Triggered immediate insights generation (for testing)")
    
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
    _insights_scheduler_running = False
    
    if responder:
        responder.close()
    if gateway:
        gateway.close()
    if insights_producer:
        insights_producer.close()
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


class InsightResponse(BaseModel):
    insight_id: str
    insight_type: str
    title: str
    description: str
    data: dict
    priority: str
    timestamp: str


class InsightsListResponse(BaseModel):
    insights: list[InsightResponse]
    count: int


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


@app.post("/insights/generate", response_model=InsightsListResponse)
async def generate_and_publish_insights():
    """
    Generate insights from order data and publish to Kafka.
    
    Returns:
        List of generated insights
    """
    try:
        logger.info("📊 API: Generating insights...")
        insights = generate_insights()
        logger.info(f"📈 API: Generated {len(insights)} insights")
        
        # Publish insights to Kafka
        published_count = publish_insights_to_kafka(insights)
        if published_count > 0:
            logger.info(f"✅ API: Published {published_count}/{len(insights)} insights to Kafka topic '{TOPICS['insights']}'")
        else:
            logger.warning(f"⚠️ API: Failed to publish insights to Kafka (0/{len(insights)} published)")
        
        # Convert to response format
        insight_responses = [
            InsightResponse(
                insight_id=str(uuid.uuid4()),
                insight_type=insight["insight_type"],
                title=insight["title"],
                description=insight["description"],
                data=insight["data"],
                priority=insight["priority"],
                timestamp=datetime.utcnow().isoformat()
            )
            for insight in insights
        ]
        
        return InsightsListResponse(insights=insight_responses, count=len(insight_responses))
        
    except Exception as e:
        logger.error(f"Error generating insights: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error generating insights: {str(e)}")


@app.get("/insights", response_model=InsightsListResponse)
async def get_insights():
    """
    Generate and return insights (without publishing to Kafka).
    Useful for frontend to fetch insights on demand.
    
    Returns:
        List of generated insights
    """
    try:
        logger.info("📊 GET /insights: Fetching insights...")
        insights = generate_insights()
        logger.info(f"📈 GET /insights: Generated {len(insights)} insights")
        
        # Convert to response format
        insight_responses = [
            InsightResponse(
                insight_id=str(uuid.uuid4()),
                insight_type=insight["insight_type"],
                title=insight["title"],
                description=insight["description"],
                data=insight["data"],
                priority=insight["priority"],
                timestamp=datetime.utcnow().isoformat()
            )
            for insight in insights
        ]
        
        return InsightsListResponse(insights=insight_responses, count=len(insight_responses))
        
    except Exception as e:
        logger.error(f"Error fetching insights: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error fetching insights: {str(e)}")


@app.post("/insights/trigger", response_model=InsightsListResponse)
async def trigger_insights_now():
    """
    Manually trigger insights generation and publish to Kafka immediately.
    Useful for testing or forcing an immediate update.
    
    Returns:
        List of generated insights
    """
    try:
        logger.info("🚀 Manual trigger: Generating insights immediately...")
        insights = generate_insights()
        logger.info(f"📈 Manual trigger: Generated {len(insights)} insights")
        
        # Publish insights to Kafka
        published_count = publish_insights_to_kafka(insights)
        if published_count > 0:
            logger.info(f"✅ Manual trigger: Published {published_count}/{len(insights)} insights to Kafka topic '{TOPICS['insights']}'")
        else:
            logger.warning(f"⚠️ Manual trigger: Failed to publish insights to Kafka (0/{len(insights)} published)")
        
        # Convert to response format
        insight_responses = [
            InsightResponse(
                insight_id=str(uuid.uuid4()),
                insight_type=insight["insight_type"],
                title=insight["title"],
                description=insight["description"],
                data=insight["data"],
                priority=insight["priority"],
                timestamp=datetime.utcnow().isoformat()
            )
            for insight in insights
        ]
        
        return InsightsListResponse(insights=insight_responses, count=len(insight_responses))
        
    except Exception as e:
        logger.error(f"Error in manual trigger: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error triggering insights: {str(e)}")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, log_level="info")

