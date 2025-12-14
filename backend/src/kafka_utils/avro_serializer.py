"""
Avro serialization utilities for Kafka events.
"""
import json
import logging
from typing import Any, Dict, Optional, Union
from confluent_kafka.schema_registry import SchemaRegistryClient
from confluent_kafka.schema_registry.avro import AvroSerializer, AvroDeserializer
from confluent_kafka.serialization import SerializationContext, MessageField
import fastavro
from io import BytesIO

from src.kafka_utils.config import get_schema_registry_config
from src.kafka_utils.avro_schemas import COMMAND_EVENT_SCHEMA, OUTPUT_EVENT_SCHEMA

logger = logging.getLogger(__name__)

# Schema Registry client (singleton)
_schema_registry_client: Optional[SchemaRegistryClient] = None


def get_schema_registry_client() -> SchemaRegistryClient:
    """Get or create Schema Registry client."""
    global _schema_registry_client
    if _schema_registry_client is None:
        config = get_schema_registry_config()
        _schema_registry_client = SchemaRegistryClient(config)
        logger.info(f"Schema Registry client initialized: {config.get('url', 'N/A')}")
    return _schema_registry_client


def register_schema(topic: str, schema_dict: Dict[str, Any], subject_suffix: str = "-value") -> Optional[int]:
    """
    Register an Avro schema in Schema Registry.
    If schema already exists, returns the existing schema ID.
    
    Args:
        topic: Kafka topic name
        schema_dict: Avro schema as dictionary
        subject_suffix: Subject suffix (usually "-value" for values, "-key" for keys)
        
    Returns:
        Schema ID from Schema Registry, or None if registration failed (will be handled by auto-register)
    """
    try:
        client = get_schema_registry_client()
        subject = f"{topic}{subject_suffix}"
        
        # Convert dict to Avro schema string
        schema_str = json.dumps(schema_dict)
        
        # Try to get existing schema first
        try:
            # Check if schema already exists
            latest_schema = client.get_latest_version(subject)
            # latest_schema is a SchemaVersion object
            if latest_schema:
                if hasattr(latest_schema, 'schema_id'):
                    schema_id = latest_schema.schema_id
                elif isinstance(latest_schema, int):
                    schema_id = latest_schema
                else:
                    # Try to extract schema_id from the object
                    schema_id = getattr(latest_schema, 'schema_id', None)
                    if schema_id is None:
                        # If we can't get schema_id, try to register anyway
                        raise ValueError("Could not extract schema_id from existing schema")
                
                logger.info(f"Schema already exists for subject '{subject}' with ID: {schema_id}")
                return int(schema_id)
        except Exception as e:
            # Schema doesn't exist (404 is expected), register it
            if "404" in str(e) or "Not Found" in str(e):
                logger.debug(f"Schema not found for subject '{subject}', will register new one")
            else:
                logger.debug(f"Error checking existing schema for '{subject}': {e}")
        
        # Register schema - try different API approaches
        schema_id = None
        try:
            # Method 1: Try with Schema object (most reliable)
            from confluent_kafka.schema_registry import Schema
            schema_obj = Schema(schema_str, schema_type='AVRO')
            schema_id = client.register_schema(subject, schema_obj)
        except (ImportError, AttributeError, TypeError) as e1:
            logger.debug(f"Schema object approach failed: {e1}, trying string approach")
            try:
                # Method 2: Try with schema string and schema_type
                schema_id = client.register_schema(subject, schema_str, schema_type='AVRO')
            except TypeError:
                try:
                    # Method 3: Try with schema string only
                    schema_id = client.register_schema(subject, schema_str)
                except Exception as e2:
                    logger.warning(f"All registration methods failed for '{subject}': {e2}")
                    # Return None - auto-register in serializer will handle it
                    return None
        except Exception as e:
            logger.warning(f"Schema registration failed for '{subject}': {e}")
            # Return None - auto-register in serializer will handle it
            return None
        
        if schema_id:
            logger.info(f"Schema registered for subject '{subject}' with ID: {schema_id}")
            return int(schema_id) if not isinstance(schema_id, int) else schema_id
        else:
            logger.warning(f"Schema registration returned None for '{subject}' - will rely on auto-register")
            return None
            
    except Exception as e:
        logger.warning(f"Failed to register schema for topic '{topic}': {e}. Will rely on auto-register in serializer.")
        # Don't raise - let the serializer's auto-register handle it
        return None


def get_avro_serializer(schema_dict: Dict[str, Any], auto_register: bool = True) -> AvroSerializer:
    """
    Get an Avro serializer for the given schema.
    
    Args:
        schema_dict: Avro schema as dictionary
        auto_register: If True, automatically register schema if not exists
        
    Returns:
        AvroSerializer instance
    """
    try:
        client = get_schema_registry_client()
        # AvroSerializer expects schema as string
        schema_str = json.dumps(schema_dict)
        
        # Configure serializer with auto-registration
        serializer_config = {}
        if auto_register:
            serializer_config['auto.register.schemas'] = True
        
        # AvroSerializer signature: AvroSerializer(schema_registry_client, schema_str, to_dict=None, conf=None)
        # to_dict is optional - if None, it will use the default conversion
        # If conf is empty, pass None instead of empty dict
        if serializer_config:
            return AvroSerializer(client, schema_str, to_dict=None, conf=serializer_config)
        else:
            return AvroSerializer(client, schema_str, to_dict=None)
    except Exception as e:
        logger.error(f"Failed to create Avro serializer: {e}", exc_info=True)
        raise


def get_avro_deserializer(schema_dict: Dict[str, Any], from_dict=None) -> AvroDeserializer:
    """
    Get an Avro deserializer for the given schema.
    
    Args:
        schema_dict: Avro schema as dictionary
        from_dict: Optional callable to convert dict to object (None uses default)
        
    Returns:
        AvroDeserializer instance
    """
    try:
        client = get_schema_registry_client()
        # AvroDeserializer expects schema as string
        schema_str = json.dumps(schema_dict)
        # AvroDeserializer signature: AvroDeserializer(schema_registry_client, schema_str, from_dict=None)
        return AvroDeserializer(client, schema_str, from_dict=from_dict)
    except Exception as e:
        logger.error(f"Failed to create Avro deserializer: {e}", exc_info=True)
        raise


def serialize_avro(data: Dict[str, Any], schema_dict: Dict[str, Any]) -> bytes:
    """
    Serialize data to Avro binary format (without Schema Registry).
    This is a fallback method if Schema Registry is not available.
    
    Args:
        data: Data dictionary to serialize
        schema_dict: Avro schema as dictionary
        
    Returns:
        Serialized bytes
    """
    try:
        # Parse schema using fastavro
        schema = fastavro.parse_schema(schema_dict)
        
        # Serialize to bytes
        bytes_writer = BytesIO()
        fastavro.schemaless_writer(bytes_writer, schema, data)
        return bytes_writer.getvalue()
    except Exception as e:
        logger.error(f"Failed to serialize Avro data: {e}")
        raise


def deserialize_avro(data: bytes, schema_dict: Dict[str, Any]) -> Dict[str, Any]:
    """
    Deserialize Avro binary data (without Schema Registry).
    This is a fallback method if Schema Registry is not available.
    
    Args:
        data: Serialized bytes
        schema_dict: Avro schema as dictionary
        
    Returns:
        Deserialized data dictionary
    """
    try:
        # Parse schema using fastavro
        schema = fastavro.parse_schema(schema_dict)
        
        # Deserialize from bytes
        bytes_reader = BytesIO(data)
        return fastavro.schemaless_reader(bytes_reader, schema)
    except Exception as e:
        logger.error(f"Failed to deserialize Avro data: {e}")
        raise

