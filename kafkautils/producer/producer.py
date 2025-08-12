"""EventBridge producer wrapper for leadgen service."""
from typing import List
from eventbridge.constants import DEFAULT_DESERIALIZATION_FORMAT, DEFAULT_HASH_FLAG
from eventbridge.emitter import AsyncEventEmitter
from kafkautils.producer.kafka_config import get_producer_config
import asyncio
import uuid

class AsyncEventEmitterWrapper:
    """Wrapper around EventBridge producer for queuing and batch sending events."""

    def __init__(self, event_emitter=None, *args, **kwargs):
        self.event_emitter = event_emitter
        self.event_queue: List = []

    def add_event_to_queue(self, *,
                           topics, partition_value,
                           event, event_meta=None,
                           serialization_format=DEFAULT_DESERIALIZATION_FORMAT,
                           hash_flag=DEFAULT_HASH_FLAG, callback=False, headers=None):
        """Add an event to the queue for batch processing."""
        if event_meta is None:
            event_meta = {}
        event_dict = {
            'topics': topics,
            'partition_value': partition_value,
            'event': event,
            'event_meta': event_meta,
            'serialization_format': serialization_format,
            'hash_flag': hash_flag,
            'callback': callback,
            'headers': headers
        }
        self.event_queue.append(event_dict)

    async def emit(self, *args, **kwargs):
        """Emit a single event immediately."""
        return await self.event_emitter.emit(*args, **kwargs)

    async def produce_event(self, *args, **kwargs):
        """Produce a single event immediately."""
        return await self.event_emitter.produce_event(*args, **kwargs)

    async def emit_events(self):
        """Emit all queued events in batch."""
        for event in self.event_queue:
            try:
                response = await self.event_emitter.emit(
                    topics=event["topics"],
                    partition_value=event["partition_value"],
                    event=event["event"],
                    event_meta=event["event_meta"],
                    serialization_format=event["serialization_format"],
                    hash_flag=event["hash_flag"],
                    callback=event["callback"],
                    headers=event["headers"]
                )
            except Exception as e:
                print(f"❌ EventEmitter error: {e}")
                # Log error but continue processing other events
        self.clear_queue()

    def clear_queue(self):
        """Clear the event queue."""
        self.event_queue = []
