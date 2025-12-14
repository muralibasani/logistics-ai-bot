import os
from pathlib import Path
from typing import Any, Dict
from dotenv import load_dotenv

load_dotenv()


def get_kafka_config() -> Dict[str, Any]:
    """Get Kafka configuration from environment variables."""
    # Get the base directory (backend)
    base_dir = Path(__file__).parent.parent.parent
    certs_dir = base_dir / "certs"
    
    # SSL configuration
    security_protocol = os.getenv("KAFKA_SECURITY_PROTOCOL", "SSL")
    config = {
        "bootstrap.servers": os.getenv("KAFKA_BOOTSTRAP_SERVERS", "localhost:9092"),
        "security.protocol": security_protocol,
    }
    
    # Add SSL configuration if using SSL
    if security_protocol in ["SSL", "SASL_SSL"]:
        # Paths to certificate files
        ca_cert = certs_dir / "ca.pem"
        client_cert = certs_dir / "service.cert"
        client_key = certs_dir / "service.key"
        ssl_password = os.getenv("KAFKA_SSL_PASSWORD", "log321")
        
        if ca_cert.exists():
            config["ssl.ca.location"] = str(ca_cert)
        if client_cert.exists():
            config["ssl.certificate.location"] = str(client_cert)
        if client_key.exists():
            config["ssl.key.location"] = str(client_key)
            config["ssl.key.password"] = ssl_password
        
        # Optional: Set SSL protocol version
        config["ssl.endpoint.identification.algorithm"] = "none"  # or "https" for hostname verification
    
    return config


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
    "commands": "events.workflow.commands",
    "output": "events.output.message",
}
