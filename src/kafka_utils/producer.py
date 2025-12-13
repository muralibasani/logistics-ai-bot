import json
import logging
from typing import Any, Dict, Optional

from confluent_kafka import Producer, KafkaError

from src.kafka_utils.config import get_producer_config

logger = logging.getLogger(__name__)


class KafkaProducer:
    """Kafka producer with JSON serialization and logging."""

    def __init__(self):
        self._producer: Optional[Producer] = None
        self._connected = False

    def connect(self) -> bool:
        """Connect to Kafka broker."""
        try:
            config = get_producer_config()
            self._producer = Producer(config)
            self._connected = True
            logger.info("Kafka producer connected successfully")
            return True
        except Exception as e:
            logger.error(f"Failed to connect Kafka producer: {e}")
            self._connected = False
            return False

    def produce(self, topic: str, message: Dict[str, Any], key: Optional[str] = None) -> bool:
        """Produce a JSON message to a Kafka topic."""
        if not self._connected or self._producer is None:
            logger.error("Producer not connected. Call connect() first.")
            return False

        try:
            json_message = json.dumps(message)
            self._producer.produce(
                topic=topic,
                key=key.encode("utf-8") if key else None,
                value=json_message.encode("utf-8"),
                callback=self._delivery_callback,
            )
            self._producer.poll(0)
            
            # Enhanced logging with clear event flow
            logger.info("=" * 80)
            logger.info(f"📤 EVENT PRODUCED → Topic: '{topic}'")
            if key:
                logger.info(f"   Key: {key}")
            logger.info(f"   Event: {json.dumps(message, indent=2)}")
            logger.info("=" * 80)
            
            return True
        except Exception as e:
            logger.error(f"Failed to produce message to '{topic}': {e}")
            return False

    def _delivery_callback(self, err: Optional[KafkaError], msg):
        """Callback for message delivery confirmation."""
        if err is not None:
            logger.error(f"Message delivery failed: {err}")
        else:
            logger.debug(f"Message delivered to {msg.topic()} [{msg.partition()}] @ {msg.offset()}")

    def flush(self, timeout: float = 10.0):
        """Flush any pending messages."""
        if self._producer:
            self._producer.flush(timeout)

    def close(self):
        """Close the producer connection."""
        if self._producer:
            self.flush()
            self._connected = False
            logger.info("Kafka producer closed")
