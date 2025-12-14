"""
Entry point for the Responder service.
Run this as a separate process to handle tool execution.
"""
import logging
from dotenv import load_dotenv
from src.responder import Responder

load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def main():
    """Main entry point for the Responder service."""
    print("")
    print("=" * 80)
    print("🔧 RESPONDER SERVICE - Starting...")
    print("=" * 80)
    print("")
    
    try:
        responder = Responder()
        logger.info("✅ Responder instance created")
        
        print("")
        print("🚀 Starting consumer...")
        print("   Make sure Kafka is running and the topic 'events.workflow.commands' exists")
        print("")
        
        responder.start_consumer()
        
    except KeyboardInterrupt:
        print("\n\n👋 Shutting down Responder...")
        logger.info("Responder shutdown requested by user")
    except Exception as e:
        print(f"\n\n❌ FATAL ERROR in Responder Service: {e}")
        logger.error(f"Fatal error in Responder: {e}", exc_info=True)
        raise
    finally:
        if 'responder' in locals():
            responder.close()
        logger.info("Responder shutdown complete")
        print("\n✅ Responder Service stopped")


if __name__ == "__main__":
    main()

