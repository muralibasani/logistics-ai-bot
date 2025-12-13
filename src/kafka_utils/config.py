import os
from typing import Any, Dict
from dotenv import load_dotenv

load_dotenv()


def get_kafka_config() -> Dict[str, Any]:
    """Get Kafka configuration from environment variables."""
    return {
        "bootstrap.servers": os.getenv("KAFKA_BOOTSTRAP_SERVERS", "localhost:9092"),
        "security.protocol": os.getenv("KAFKA_SECURITY_PROTOCOL", "PLAINTEXT"),
    }


def get_producer_config() -> Dict[str, Any]:
    """Get Kafka producer configuration."""
    config: Dict[str, Any] = get_kafka_config()
    config.update({
        "acks": "all",
        "retries": 3,
        "retry.backoff.ms": 1000,
    })
    return config


def get_consumer_config(group_id: str) -> Dict[str, Any]:
    """Get Kafka consumer configuration with specified group ID."""
    config: Dict[str, Any] = get_kafka_config()
    config.update({
        "group.id": group_id,
        "auto.offset.reset": os.getenv("KAFKA_AUTO_OFFSET_RESET", "earliest"),
        "enable.auto.commit": True,
        "auto.commit.interval.ms": 5000,
        "session.timeout.ms": 30000,
        "heartbeat.interval.ms": 10000,
    })
    return config


TOPICS = {
    "raw_input": "events.input.raw",
    "classified": "events.input.classified",
    "commands": "events.workflow.commands",
    "output": "events.output.message",
}
