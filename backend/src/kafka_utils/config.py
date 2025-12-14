import os
import logging
from pathlib import Path
from typing import Any, Dict
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)


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
            config["ssl.ca.location"] = str(ca_cert.absolute())
        else:
            logger.warning(f"CA certificate not found at: {ca_cert.absolute()}")
        if client_cert.exists():
            config["ssl.certificate.location"] = str(client_cert.absolute())
        else:
            logger.warning(f"Client certificate not found at: {client_cert.absolute()}")
        if client_key.exists():
            config["ssl.key.location"] = str(client_key.absolute())
            config["ssl.key.password"] = ssl_password
        else:
            logger.warning(f"Client key not found at: {client_key.absolute()}")
        
        # Optional: Set SSL protocol version
        config["ssl.endpoint.identification.algorithm"] = "none"  # or "https" for hostname verification
        
        # Additional network settings for better connection handling
        config["socket.timeout.ms"] = 60000  # 60 seconds
        config["metadata.request.timeout.ms"] = 60000
        config["api.version.request.timeout.ms"] = 60000
    
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
    "insights": "events.insights.message",
}


def get_schema_registry_url() -> str:
    """Get Schema Registry URL from environment variables."""
    return os.getenv("KAFKA_SCHEMA_REGISTRY_URL", "http://localhost:8081")


def get_schema_registry_config() -> Dict[str, Any]:
    """Get Schema Registry configuration."""
    schema_registry_url = get_schema_registry_url()
    
    # Extract credentials from URL if present (format: https://user:pass@host:port)
    config = {}
    
    # If URL contains credentials, extract them
    if "@" in schema_registry_url:
        # Format: https://user:pass@host:port
        parts = schema_registry_url.split("@")
        if len(parts) == 2:
            auth_part = parts[0].split("//")[-1]
            if ":" in auth_part:
                username, password = auth_part.split(":", 1)
                config["basic.auth.user.info"] = f"{username}:{password}"
            # Extract the base URL without credentials
            protocol = schema_registry_url.split("//")[0]
            host_part = parts[1]
            config["url"] = f"{protocol}//{host_part}"
        else:
            config["url"] = schema_registry_url
    else:
        config["url"] = schema_registry_url
    
    return config
