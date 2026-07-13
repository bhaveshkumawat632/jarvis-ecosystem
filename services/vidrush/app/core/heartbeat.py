import time
import asyncio
import structlog
from app.core.event_bus import event_bus

logger = structlog.get_logger(__name__)

class WorkerHeartbeat:
    """Maintains liveness pings for distributed processes across the cluster."""
    def __init__(self, worker_id: str, service_type: str):
        self.worker_id = worker_id
        self.service_type = service_type
        self.interval = 10  # Seconds
        self._running = False

    async def start_heartbeat(self):
        self._running = True
        await event_bus.publish("WORKER_ONLINE", payload={"worker_id": self.worker_id, "service": self.service_type})
        logger.info("worker_online", worker_id=self.worker_id, service=self.service_type)
        
        while self._running:
            await event_bus.publish("WORKER_HEARTBEAT", payload={
                "worker_id": self.worker_id,
                "timestamp": time.time(),
                "status": "healthy"
            })
            await asyncio.sleep(self.interval)

    async def stop_heartbeat(self, degraded: bool = False):
        self._running = False
        state = "WORKER_DEGRADED" if degraded else "WORKER_OFFLINE"
        await event_bus.publish(state, payload={"worker_id": self.worker_id, "service": self.service_type})
