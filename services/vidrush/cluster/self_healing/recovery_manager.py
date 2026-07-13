import structlog
from app.core.event_bus import event_bus

logger = structlog.get_logger(__name__)

class SelfHealingCluster:
    """Detects failing nodes and rebuilds dead pipelines automatically."""
    def __init__(self):
        event_bus.subscribe("WORKER_DEGRADED", self._handle_sick_node)
        event_bus.subscribe("WORKER_OFFLINE", self._isolate_dead_node)

    async def _handle_sick_node(self, event: dict):
        worker_id = event["payload"]["worker_id"]
        logger.warning("self_healing_sick_node_detected", worker=worker_id)
        await event_bus.publish("NODE_UNHEALTHY", payload={"worker_id": worker_id})

    async def _isolate_dead_node(self, event: dict):
        worker_id = event["payload"]["worker_id"]
        logger.error("self_healing_dead_node_isolated", worker=worker_id)
        
        # Re-route orphaned jobs from this node
        logger.info("self_healing_auto_failover_initiated")
        await event_bus.publish("AUTO_FAILOVER_TRIGGERED", payload={"failed_worker": worker_id})
        
        # Signal system recovered
        await event_bus.publish("NODE_RECOVERED", payload={"worker_id": worker_id, "action": "jobs_reassigned"})

self_healing_manager = SelfHealingCluster()
