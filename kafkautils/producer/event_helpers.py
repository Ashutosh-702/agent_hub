"""Event emission helpers following pigeon pattern."""
import asyncio
from typing import Dict, Any, List
from kafkautils.producer.producer import AsyncEventEmitterWrapper
from kafkautils.constants import LEADGEN_BATCH_PROCESSING


async def emit_event_helper(event_emitter: AsyncEventEmitterWrapper = None,
                            topics: List[str] = None,
                            partition_value: str = None,
                            event: dict = None,
                            event_meta: dict = None):
    """Helper function to emit events directly (like pigeon pattern)."""
    try:
        result = await event_emitter.emit(
            topics=topics or [LEADGEN_BATCH_PROCESSING],
            partition_value=partition_value,
            event=event,
            event_meta=event_meta or {},
            serialization_format="json",
            hash_flag=True
        )
        
        print(f"✅ Event emitted: {partition_value}")
        return result
        
    except Exception as e:
        print(f"❌ Event emission failed: {e}")
        import traceback
        traceback.print_exc()
        # You can add contextvars binding here like pigeon does
        raise


async def queue_and_emit_helper(event_emitter: AsyncEventEmitterWrapper = None,
                                topics: List[str] = None,
                                partition_value: str = None,
                                event: dict = None,
                                event_meta: dict = None):
    """Helper function to queue and batch emit events (pigeon pattern)."""
    try:
        # Add to queue (like pigeon's add_event_to_queue)
        event_emitter.add_event_to_queue(
            topics=topics or [LEADGEN_BATCH_PROCESSING],
            partition_value=partition_value,
            event=event,
            event_meta=event_meta or {},
            serialization_format="json",
            hash_flag=True
        )
        
        # Emit all queued events
        await event_emitter.emit_events()
        print(f"✅ Batch event emitted: {partition_value}")
        
    except Exception as e:
        print(f"❌ Batch event emission failed: {e}")
        raise 