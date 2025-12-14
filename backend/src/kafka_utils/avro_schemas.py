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

INSIGHT_EVENT_SCHEMA = {
    "type": "record",
    "name": "InsightEvent",
    "namespace": "com.logistics.events",
    "fields": [
        {"name": "insight_id", "type": "string"},
        {"name": "insight_type", "type": "string"},
        {"name": "title", "type": "string"},
        {"name": "description", "type": "string"},
        {"name": "data", "type": {"type": "map", "values": "string"}},
        {"name": "priority", "type": {"type": "enum", "name": "Priority", "symbols": ["low", "medium", "high"]}},
        {"name": "timestamp", "type": "string"}
    ]
}

