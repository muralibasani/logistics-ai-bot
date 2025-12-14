import json
import logging
import time
from typing import Any, Callable, Dict, List, Optional

from confluent_kafka import Consumer, KafkaError, KafkaException
from confluent_kafka.serialization import SerializationContext, MessageField

from src.kafka_utils.config import get_consumer_config, TOPICS
from src.kafka_utils.avro_serializer import (
    get_avro_deserializer,
    deserialize_avro
)
from src.kafka_utils.avro_schemas import COMMAND_EVENT_SCHEMA, OUTPUT_EVENT_SCHEMA

logger = logging.getLogger(__name__)


class KafkaConsumer:
    """Kafka consumer with auto-reconnect and backoff retry logic."""

    def __init__(self, group_id: str, topics: List[str]):
        self.group_id = group_id
        self.topics = topics
        self._consumer: Optional[Consumer] = None
        self._connected = False
        self._running = False
        self._max_retries = 5
        self._base_backoff = 1.0
        self._max_backoff = 60.0
        self._command_deserializer = None
        self._output_deserializer = None
        self._deserializers_initialized = False

    def connect(self) -> bool:
        """Connect to Kafka broker with retry logic and initialize Avro deserializers."""
        retries = 0
        while retries < self._max_retries:
            try:
                config = get_consumer_config(self.group_id)
                self._consumer = Consumer(config)
                self._consumer.subscribe(self.topics)
                self._connected = True
                logger.info(f"Kafka consumer connected. Subscribed to: {self.topics}")
                
                # Initialize Avro deserializers
                if not self._deserializers_initialized:
                    try:
                        self._command_deserializer = get_avro_deserializer(COMMAND_EVENT_SCHEMA)
                        self._output_deserializer = get_avro_deserializer(OUTPUT_EVENT_SCHEMA)
                        self._deserializers_initialized = True
                        logger.info("Avro deserializers initialized")
                    except Exception as e:
                        logger.warning(f"Failed to initialize Avro deserializers: {e}. Using fallback deserialization.")
                        # Continue without Schema Registry - will use direct Avro deserialization
                
                return True
            except Exception as e:
                retries += 1
                backoff = min(self._base_backoff * (2 ** retries), self._max_backoff)
                logger.error(f"Failed to connect (attempt {retries}/{self._max_retries}): {e}")
                if retries < self._max_retries:
                    logger.info(f"Retrying in {backoff:.1f} seconds...")
                    time.sleep(backoff)

        logger.error("Max retries reached. Could not connect to Kafka.")
        return False

    def consume(
        self,
        message_handler: Callable[[Dict[str, Any]], None],
        poll_timeout: float = 1.0,
    ):
        """
        Start consuming messages in an infinite loop.
        
        Args:
            message_handler: Callback function to process each message
            poll_timeout: Timeout in seconds for each poll
        """
        if not self._connected or self._consumer is None:
            logger.error("Consumer not connected. Call connect() first.")
            return

        self._running = True
        consecutive_errors = 0

        logger.info(f"Starting consumer loop for topics: {self.topics}")

        while self._running:
            try:
                msg = self._consumer.poll(poll_timeout)

                if msg is None:
                    continue

                if msg.error():
                    if msg.error().code() == KafkaError._PARTITION_EOF:
                        logger.debug(f"Reached end of partition {msg.partition()}")
                    else:
                        logger.error(f"Kafka error: {msg.error()}")
                        raise KafkaException(msg.error())
                    continue

                consecutive_errors = 0
                value = msg.value()
                
                if value:
                    try:
                        # Deserialize Avro message
                        topic = msg.topic()
                        if topic == TOPICS["commands"]:
                            schema = COMMAND_EVENT_SCHEMA
                            deserializer = self._command_deserializer
                        elif topic == TOPICS["output"]:
                            schema = OUTPUT_EVENT_SCHEMA
                            deserializer = self._output_deserializer
                        else:
                            logger.error(f"Unknown topic '{topic}'. Cannot determine schema.")
                            continue
                        
                        if deserializer:
                            # Use Schema Registry deserializer
                            context = SerializationContext(topic, MessageField.VALUE)
                            avro_message = deserializer(value, context)
                        else:
                            # Fallback: direct Avro deserialization
                            avro_message = deserialize_avro(value, schema)
                        
                        logger.info(f"📥 [CONSUMER] Received Avro message from topic '{topic}'")
                        message_handler(avro_message)
                    except Exception as e:
                        logger.error(f"Failed to deserialize Avro message: {e}", exc_info=True)

            except KafkaException as e:
                consecutive_errors += 1
                backoff = min(self._base_backoff * (2 ** consecutive_errors), self._max_backoff)
                logger.error(f"Kafka error: {e}. Retrying in {backoff:.1f}s...")
                time.sleep(backoff)

                if consecutive_errors >= self._max_retries:
                    logger.warning("Too many consecutive errors. Attempting reconnect...")
                    self._reconnect()
                    consecutive_errors = 0

            except Exception as e:
                logger.error(f"Unexpected error in consumer loop: {e}", exc_info=True)
                time.sleep(1)

    def _reconnect(self):
        """Attempt to reconnect the consumer."""
        logger.info("Attempting to reconnect consumer...")
        self.close()
        time.sleep(2)
        self.connect()

    def stop(self):
        """Stop the consumer loop."""
        self._running = False
        logger.info("Consumer stop requested")

    def close(self):
        """Close the consumer connection."""
        if self._consumer:
            try:
                self._consumer.close()
            except Exception as e:
                logger.error(f"Error closing consumer: {e}")
            self._connected = False
            logger.info("Kafka consumer closed")
