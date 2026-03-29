import logging
import os
from functools import lru_cache
from typing import Protocol

from app.modules.events.schemas import StandardEvent


logger = logging.getLogger(__name__)


class EventStream(Protocol):
    def publish(self, event: StandardEvent) -> None:
        ...


class InMemoryEventStream:
    def __init__(self):
        self._buffer: list[StandardEvent] = []

    def publish(self, event: StandardEvent) -> None:
        self._buffer.append(event)

    def snapshot(self) -> list[StandardEvent]:
        return list(self._buffer)


class KafkaCompatibleEventStream:
    """
    Thin adapter placeholder to keep a Kafka-compatible boundary.
    In production, replace internals by a concrete producer (Kafka/Redpanda/etc).
    """

    def __init__(self, topic: str):
        self.topic = topic

    def publish(self, event: StandardEvent) -> None:
        logger.info(
            "event_stream_publish",
            extra={
                "topic": self.topic,
                "event_id": event.event_id,
                "event_type": event.event_type,
                "tenant_id": event.tenant_id,
                "merchant_id": event.merchant_id,
                "correlation_id": event.correlation_id,
                "trace_id": event.trace_id,
            },
        )


@lru_cache(maxsize=1)
def get_event_stream() -> EventStream:
    backend = os.getenv("EVENT_STREAM_BACKEND", "memory").strip().lower()
    if backend == "kafka":
        topic = os.getenv("EVENT_STREAM_TOPIC", "anexi.events")
        return KafkaCompatibleEventStream(topic=topic)
    return InMemoryEventStream()

