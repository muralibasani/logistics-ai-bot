import json
import logging
from typing import Any, Dict, Optional

from confluent_kafka import Producer, KafkaError
from confluent_kafka.serialization import SerializationContext, MessageField

from src.kafka_utils.config import get_producer_config, TOPICS
from src.kafka_utils.avro_serializer import (
    get_avro_serializer,
    register_schema,
    serialize_avro
)
from src.kafka_utils.avro_schemas import COMMAND_EVENT_SCHEMA, OUTPUT_EVENT_SCHEMA, INSIGHT_EVENT_SCHEMA

logger = logging.getLogger(__name__)


class KafkaProducer:
    """Kafka producer with Avro serialization and logging."""

    def __init__(self):
        self._producer: Optional[Producer] = None
        self._connected = False
        self._command_serializer = None
        self._output_serializer = None
        self._insight_serializer = None
        self._schemas_registered = False

    def connect(self) -> bool:
        """Connect to Kafka broker and register Avro schemas."""
        try:
            config = get_producer_config()
            logger.info(f"Connecting to Kafka with bootstrap servers: {config.get('bootstrap.servers')}")
            logger.debug(f"Full Kafka config: {config}")
            self._producer = Producer(config)
            # Note: Producer creation is lazy - actual connection happens on first produce
            self._connected = True
            logger.info("Kafka producer created successfully (lazy connection)")
            
            # Register schemas and create serializers (defer to first produce to avoid early connection issues)
            # We'll initialize serializers lazily on first produce call
            
            return True
        except Exception as e:
            logger.error(f"Failed to connect Kafka producer: {e}")
            self._connected = False
            return False

    def produce(self, topic: str, message: Dict[str, Any], key: Optional[str] = None) -> bool:
        """Produce an Avro message to a Kafka topic."""
        if not self._connected or self._producer is None:
            logger.error("Producer not connected. Call connect() first.")
            return False

        try:
            # Initialize serializers on first use (lazy initialization)
            if not self._schemas_registered:
                try:
                    # Try to register schemas explicitly first (for logging/debugging)
                    # This is optional - auto-register in serializer will handle it if this fails
                    cmd_schema_id = register_schema(TOPICS["commands"], COMMAND_EVENT_SCHEMA)
                    output_schema_id = register_schema(TOPICS["output"], OUTPUT_EVENT_SCHEMA)
                    insight_schema_id = register_schema(TOPICS["insights"], INSIGHT_EVENT_SCHEMA)
                    
                    if cmd_schema_id and output_schema_id and insight_schema_id:
                        logger.info(f"Schemas pre-registered: commands={cmd_schema_id}, output={output_schema_id}, insights={insight_schema_id}")
                    else:
                        logger.info("Schemas will be auto-registered by serializer on first use")
                    
                    # Create Avro serializers with auto-registration enabled
                    # This ensures schemas are registered even if pre-registration failed
                    self._command_serializer = get_avro_serializer(COMMAND_EVENT_SCHEMA, auto_register=True)
                    self._output_serializer = get_avro_serializer(OUTPUT_EVENT_SCHEMA, auto_register=True)
                    self._insight_serializer = get_avro_serializer(INSIGHT_EVENT_SCHEMA, auto_register=True)
                    
                    self._schemas_registered = True
                    logger.info("Avro serializers created with auto-registration enabled")
                except Exception as e:
                    logger.warning(f"Failed to create serializers: {e}. Using fallback serialization.", exc_info=True)
                    # Continue without Schema Registry - will use direct Avro serialization
                    self._schemas_registered = True  # Mark as attempted to avoid retrying on every produce
            
            # Determine which schema and serializer to use
            if topic == TOPICS["commands"]:
                schema = COMMAND_EVENT_SCHEMA
                serializer = self._command_serializer
            elif topic == TOPICS["output"]:
                schema = OUTPUT_EVENT_SCHEMA
                serializer = self._output_serializer
            elif topic == TOPICS["insights"]:
                schema = INSIGHT_EVENT_SCHEMA
                serializer = self._insight_serializer
            else:
                logger.error(f"Unknown topic '{topic}'. Cannot determine schema.")
                return False
            
            # Serialize message to Avro
            if serializer:
                # Use Schema Registry serializer
                context = SerializationContext(topic, MessageField.VALUE)
                avro_bytes = serializer(message, context)
            else:
                # Fallback: direct Avro serialization
                avro_bytes = serialize_avro(message, schema)
            
            # Produce to Kafka
            self._producer.produce(
                topic=topic,
                key=key.encode("utf-8") if key else None,
                value=avro_bytes,
                callback=self._delivery_callback,
            )
            self._producer.poll(0)
            
            logger.debug(f"Avro message produced to topic '{topic}'")
            return True
        except Exception as e:
            logger.error(f"Failed to produce Avro message to '{topic}': {e}", exc_info=True)
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
