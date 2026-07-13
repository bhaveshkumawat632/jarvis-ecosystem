import structlog
from typing import Dict

logger = structlog.get_logger(__name__)

class ProcessRegistry:
    """Central registry tracking multi-process worker isolated states via Redis-backed syncing."""
    def __init__(self):
        self.workers: Dict[str, dict] = {}

    def register(self, worker_id: str, service_type: str, node_id: str):
        self.workers[worker_id] = {
            "service_type": service_type,
            "node_id": node_id,
            "status": "starting",
            "last_heartbeat": 0
        }
        logger.info("process_registered", worker_id=worker_id, service=service_type, node=node_id)

    def update_status(self, worker_id: str, status: str, heartbeat_timestamp: float):
        if worker_id in self.workers:
            self.workers[worker_id]["status"] = status
            self.workers[worker_id]["last_heartbeat"] = heartbeat_timestamp

registry = ProcessRegistry()
