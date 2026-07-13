import asyncio
import uuid
import structlog
from typing import Callable, Dict, List, Any

logger = structlog.get_logger(__name__)

class EventBus:
    def __init__(self):
        self.subscribers: Dict[str, List[Callable]] = {}
        self.queue: asyncio.Queue = asyncio.Queue()
        self._running = False
        self._dispatch_task = None

    def subscribe(self, event_type: str, callback: Callable):
        if event_type not in self.subscribers:
            self.subscribers[event_type] = []
        self.subscribers[event_type].append(callback)
        logger.info("event_subscribed", event_name=event_type, callback=callback.__name__)

    async def publish(self, event_type: str, payload: Any = None, task_id: str = None):
        if not task_id:
            task_id = str(uuid.uuid4())
        
        event = {
            "type": event_type,
            "payload": payload,
            "task_id": task_id
        }
        await self.queue.put(event)
        logger.info("event_published", event_name=event_type, task_id=task_id)

    async def _dispatch_loop(self):
        self._running = True
        logger.info("event_bus_started")
        while self._running:
            event = await self.queue.get()
            event_type = event["type"]
            if event_type in self.subscribers:
                for callback in self.subscribers[event_type]:
                    try:
                        # Dispatch asynchronously
                        asyncio.create_task(self._safe_execute(callback, event))
                    except Exception as e:
                        logger.error("dispatch_error", event_name=event_type, error=str(e))
            self.queue.task_done()

    async def _safe_execute(self, callback: Callable, event: dict):
        try:
            if asyncio.iscoroutinefunction(callback):
                await callback(event)
            else:
                callback(event)
        except Exception as e:
            logger.error("callback_failed", event_name=event["type"], error=str(e))
            # Retry propagation can be signaled back to the bus here
            await self.publish("WORKFLOW_ERROR", payload={"error": str(e), "original_event": event}, task_id=event["task_id"])

    def start(self):
        if not self._dispatch_task:
            self._dispatch_task = asyncio.create_task(self._dispatch_loop())

    async def stop(self):
        self._running = False
        if self._dispatch_task:
            self._dispatch_task.cancel()

# Global Event Bus Singleton
event_bus = EventBus()
