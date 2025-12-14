"""
Avro schemas for Kafka events.
"""
COMMAND_EVENT_SCHEMA = {
    "type": "record",
    "name": "CommandEvent",
    "namespace": "com.logistics.events",
    "fields": [
        {"name": "message_id", "type": "string"},
        {"name": "tool_name", "type": "string"},
        {"name": "message", "type": "string"},
        {"name": "timestamp", "type": "string"}
    ]
}

OUTPUT_EVENT_SCHEMA = {
    "type": "record",
    "name": "OutputEvent",
    "namespace": "com.logistics.events",
    "fields": [
        {"name": "message_id", "type": "string"},
        {"name": "response", "type": "string"},
        {"name": "tool_name", "type": "string"},
        {"name": "timestamp", "type": "string"}
    ]
}

