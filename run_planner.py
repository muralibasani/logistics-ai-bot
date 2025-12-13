"""
Entry point for the Planner service.
Run this as a separate process to handle message classification.
"""
import logging
from dotenv import load_dotenv
from src.planner import Planner

load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def main():
    """Main entry point for the Planner service."""
    print("📋 Starting Planner Service...")
    print("=" * 60)
    
    planner = Planner()
    
    try:
        planner.start_consumer()
    except KeyboardInterrupt:
        print("\n\n👋 Shutting down Planner...")
    finally:
        planner.close()
        logger.info("Planner shutdown complete")


if __name__ == "__main__":
    main()

