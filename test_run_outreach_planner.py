"""
Test script to produce Kafka messages for run_outreach_planner_handler

This script sends a test message to the 'run_outreach_planner' Kafka topic
to trigger the outreach planner execution.

Usage:
    python test_run_outreach_planner.py
"""
import asyncio
import json
import uuid
from datetime import datetime
from kafka import KafkaProducer
from kafka.errors import KafkaError
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


def test_run_outreach_planner_producer():
    """Send test message to run_outreach_planner topic"""
    
    # Kafka configuration
    bootstrap_servers = os.getenv("KAFKA_BROKER_LIST", "localhost:9092").split(",")
    topic = 'run_outreach_planner'
    
    print(f"🚀 Kafka Producer initialized")
    print(f"   Bootstrap servers: {bootstrap_servers}")
    print(f"   Topic: {topic}")
    print()
    
    # Create producer
    producer = KafkaProducer(
        bootstrap_servers=bootstrap_servers,
        value_serializer=lambda v: json.dumps(v).encode('utf-8'),
        key_serializer=lambda k: k.encode('utf-8') if k else None
    )
    
    # Test message payload (matching handler expectations)
    # Based on run_outreach_planner_handler in handlers.py (lines 380-410)
    test_message = {
        "payload": {
            "request_id": f"test_request_{uuid.uuid4().hex[:8]}",
            "action": "run_planner"  # Must be "run_planner" to match handler
        }
    }
    
    print("📨 Sending test message:")
    print(json.dumps(test_message, indent=2))
    print()
    
    try:
        # Send message
        # Using partition_value as key (can be any string for this handler)
        partition_value = f"test_planner_{int(datetime.now().timestamp())}"
        
        future = producer.send(
            topic=topic,
            key=partition_value,
            value=test_message
        )
        
        # Wait for confirmation
        record_metadata = future.get(timeout=10)
        
        print(f"✅ Message sent successfully!")
        print(f"   Topic: {record_metadata.topic}")
        print(f"   Partition: {record_metadata.partition}")
        print(f"   Offset: {record_metadata.offset}")
        print(f"   Key: {partition_value}")
        print()
        print("📋 Next steps:")
        print("   1. Check your Kafka consumer logs to see if the message was received")
        print("   2. Verify that run_outreach_planner_handler was called")
        print("   3. Check planner_chronos.log for planner execution logs")
        
    except KafkaError as e:
        print(f"❌ Failed to send message: {e}")
        return False
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    finally:
        producer.close()
        print("\n🔌 Producer closed")
    
    return True


def test_minimal_message():
    """Send minimal test message (just action)"""
    
    bootstrap_servers = os.getenv("KAFKA_BROKER_LIST", "localhost:9092").split(",")
    topic = 'run_outreach_planner'
    
    producer = KafkaProducer(
        bootstrap_servers=bootstrap_servers,
        value_serializer=lambda v: json.dumps(v).encode('utf-8'),
        key_serializer=lambda k: k.encode('utf-8') if k else None
    )
    
    # Minimal message - handler only requires action
    minimal_message = {
        "payload": {
            "action": "run_planner"
        }
    }
    
    print("📨 Sending minimal test message:")
    print(json.dumps(minimal_message, indent=2))
    print()
    
    try:
        future = producer.send(
            topic=topic,
            key="minimal_test",
            value=minimal_message
        )
        
        record_metadata = future.get(timeout=10)
        print(f"✅ Minimal message sent successfully!")
        print(f"   Topic: {record_metadata.topic}")
        print(f"   Partition: {record_metadata.partition}")
        print(f"   Offset: {record_metadata.offset}")
        
    except Exception as e:
        print(f"❌ Failed: {e}")
        return False
    finally:
        producer.close()
    
    return True


def test_invalid_action():
    """Test with invalid action (should be rejected by handler)"""
    
    bootstrap_servers = os.getenv("KAFKA_BROKER_LIST", "localhost:9092").split(",")
    topic = 'run_outreach_planner'
    
    producer = KafkaProducer(
        bootstrap_servers=bootstrap_servers,
        value_serializer=lambda v: json.dumps(v).encode('utf-8'),
        key_serializer=lambda k: k.encode('utf-8') if k else None
    )
    
    # Invalid action - should be rejected
    invalid_message = {
        "payload": {
            "request_id": f"test_invalid_{uuid.uuid4().hex[:8]}",
            "action": "invalid_action"  # This should be rejected
        }
    }
    
    print("📨 Sending message with invalid action (should be rejected):")
    print(json.dumps(invalid_message, indent=2))
    print()
    
    try:
        future = producer.send(
            topic=topic,
            key="invalid_test",
            value=invalid_message
        )
        
        record_metadata = future.get(timeout=10)
        print(f"✅ Message sent (but handler should reject it)")
        print(f"   Topic: {record_metadata.topic}")
        print(f"   Partition: {record_metadata.partition}")
        print(f"   Offset: {record_metadata.offset}")
        print()
        print("⚠️  Check consumer logs - should see 'Unknown action: invalid_action'")
        
    except Exception as e:
        print(f"❌ Failed: {e}")
        return False
    finally:
        producer.close()
    
    return True


if __name__ == "__main__":
    print("=" * 60)
    print("Run Outreach Planner Kafka Producer Test")
    print("=" * 60)
    print()
    
    choice = input(
        "Choose test:\n"
        "1. Full test message (with request_id)\n"
        "2. Minimal message (action only)\n"
        "3. Invalid action test (should be rejected)\n"
        "4. Run all tests\n"
        "Enter 1, 2, 3, or 4: "
    )
    
    print()
    
    if choice == "1":
        test_run_outreach_planner_producer()
    elif choice == "2":
        test_minimal_message()
    elif choice == "3":
        test_invalid_action()
    elif choice == "4":
        print("🧪 Running all tests...\n")
        print("=" * 60)
        print("Test 1: Full message")
        print("=" * 60)
        test_run_outreach_planner_producer()
        print("\n" + "=" * 60)
        print("Test 2: Minimal message")
        print("=" * 60)
        test_minimal_message()
        print("\n" + "=" * 60)
        print("Test 3: Invalid action")
        print("=" * 60)
        test_invalid_action()
        print("\n" + "=" * 60)
        print("✅ All tests completed!")
    else:
        print("Invalid choice. Running full test...")
        test_run_outreach_planner_producer()

