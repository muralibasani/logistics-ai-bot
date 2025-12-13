import asyncio
import logging
import threading
from contextlib import asynccontextmanager
from typing import Callable, Dict, List, Optional, Any

from src.kafka_utils.producer import KafkaProducer
from src.kafka_utils.consumer import KafkaConsumer

logger = logging.getLogger(__name__)


class KafkaConnectionManager:
    """Manages Kafka producer and consumer connections with lifecycle management."""

    def __init__(self):
        self._producer: Optional[KafkaProducer] = None
        self._consumers: Dict[str, KafkaConsumer] = {}
        self._consumer_threads: Dict[str, threading.Thread] = {}
        self._connected = False
        self._event_loop: Optional[asyncio.AbstractEventLoop] = None

    def connect_producer(self) -> bool:
        """Connect the Kafka producer."""
        if self._producer is None:
            self._producer = KafkaProducer()
        
        if not self._producer._connected:
            success = self._producer.connect()
            if success:
                logger.info("Kafka producer connected via connection manager")
            return success
        return True

    def connect_consumer(
        self,
        consumer_id: str,
        group_id: str,
        topics: List[str],
        message_handler: Callable[[Dict[str, Any]], None],
        daemon: bool = True
    ) -> bool:
        """
        Connect a Kafka consumer and start consuming in a background thread.
        
        Args:
            consumer_id: Unique identifier for this consumer
            group_id: Kafka consumer group ID
            topics: List of topics to subscribe to
            message_handler: Callback function to process messages
            daemon: Whether the consumer thread should be a daemon thread
        """
        if consumer_id in self._consumers:
            logger.warning(f"Consumer {consumer_id} already exists")
            return True

        consumer = KafkaConsumer(group_id=group_id, topics=topics)
        
        if not consumer.connect():
            logger.error(f"Failed to connect consumer {consumer_id}")
            return False

        self._consumers[consumer_id] = consumer

        def consume_messages():
            """Background thread function to consume messages."""
            logger.info(f"Starting consumer thread for {consumer_id}")
            consumer.consume(message_handler)

        thread = threading.Thread(target=consume_messages, daemon=daemon, name=f"kafka-consumer-{consumer_id}")
        thread.start()
        self._consumer_threads[consumer_id] = thread

        logger.info(f"Consumer {consumer_id} connected and started via connection manager")
        return True

    def disconnect_consumer(self, consumer_id: str):
        """Disconnect and stop a specific consumer."""
        if consumer_id in self._consumers:
            consumer = self._consumers[consumer_id]
            consumer.stop()
            consumer.close()
            del self._consumers[consumer_id]
            logger.info(f"Consumer {consumer_id} disconnected")

        if consumer_id in self._consumer_threads:
            thread = self._consumer_threads[consumer_id]
            if thread.is_alive():
                thread.join(timeout=5.0)
            del self._consumer_threads[consumer_id]

    def disconnect_all(self):
        """Disconnect all consumers and the producer."""
        # Stop all consumers
        for consumer_id in list(self._consumers.keys()):
            self.disconnect_consumer(consumer_id)

        # Close producer
        if self._producer:
            self._producer.close()
            self._producer = None
            logger.info("Kafka producer disconnected via connection manager")

        self._connected = False

    def get_producer(self) -> Optional[KafkaProducer]:
        """Get the managed producer instance."""
        return self._producer

    def get_consumer(self, consumer_id: str) -> Optional[KafkaConsumer]:
        """Get a managed consumer instance by ID."""
        return self._consumers.get(consumer_id)

    def set_event_loop(self, loop: asyncio.AbstractEventLoop):
        """Set the event loop for async operations."""
        self._event_loop = loop

    def is_connected(self) -> bool:
        """Check if producer is connected."""
        return self._producer is not None and self._producer._connected

    @asynccontextmanager
    async def lifespan(self):
        """Async context manager for managing Kafka connections lifecycle."""
        self._event_loop = asyncio.get_running_loop()
        self._connected = True

        if not self.connect_producer():
            logger.error("Failed to connect Kafka producer during lifespan")
        else:
            logger.info("Kafka connection manager initialized")

        yield

        self.disconnect_all()
        logger.info("Kafka connection manager shutdown complete")


