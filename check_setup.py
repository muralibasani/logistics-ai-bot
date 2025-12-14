"""
Quick script to check if Kafka topics exist and verify setup.
"""
import os
from dotenv import load_dotenv
from confluent_kafka import Consumer, KafkaError
from src.kafka_utils.config import TOPICS, get_kafka_config

load_dotenv()

def check_kafka_connection():
    """Check if Kafka is accessible."""
    print("=" * 80)
    print("🔍 Checking Kafka Setup...")
    print("=" * 80)
    print()
    
    try:
        config = get_kafka_config()
        print(f"✅ Kafka Config:")
        print(f"   Bootstrap Servers: {config.get('bootstrap.servers')}")
        print(f"   Security Protocol: {config.get('security.protocol')}")
        print()
        
        # Try to create a consumer to test connection
        test_config = config.copy()
        test_config.update({
            "group.id": "test-connection-group",
            "auto.offset.reset": "earliest",
        })
        
        print("🔌 Testing Kafka connection...")
        consumer = Consumer(test_config)
        print("✅ Consumer created successfully")
        
        # Try to subscribe to see if we can connect
        topics_to_check = [TOPICS["commands"], TOPICS["output"]]
        print(f"\n📋 Checking topics: {topics_to_check}")
        consumer.subscribe(topics_to_check)
        print("✅ Successfully subscribed to topics")
        
        # Poll once to see if we get any response
        print("\n🔄 Polling once to verify connection...")
        msg = consumer.poll(2.0)
        
        if msg is None:
            print("✅ Poll successful (no messages, but connection works)")
        elif msg.error():
            if msg.error().code() == KafkaError._PARTITION_EOF:
                print("✅ Connection works (reached end of partition)")
            else:
                print(f"⚠️  Got error: {msg.error()}")
        else:
            print("✅ Connection works (received a message)")
        
        consumer.close()
        # print("\n✅ Kafka connection test PASSED")
        # print()
        # print("=" * 80)
        # print("📝 Next Steps:")
        # print("=" * 80)
        # print("1. Make sure you have TWO terminals open:")
        # print("   Terminal 1: Run 'python run_responder.py'")
        # print("   Terminal 2: Run 'python main.py'")
        # print()
        # print("2. The Responder should show logs like:")
        # print("   '🚀 [CONSUMER] Starting consumer loop'")
        # print("   '🔄 [CONSUMER] First poll (#1) - waiting for messages...'")
        # print()
        # print("3. If you don't see Responder logs, it's not running!")
        # print("=" * 80)
        
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        print("\nTroubleshooting:")
        print("1. Is Kafka running? Check with: kafka-topics --list --bootstrap-server localhost:9092")
        print("2. Are the topics created?")
        print("3. Check your KAFKA_BOOTSTRAP_SERVERS environment variable")
        return False
    
    return True

if __name__ == "__main__":
    check_kafka_connection()

