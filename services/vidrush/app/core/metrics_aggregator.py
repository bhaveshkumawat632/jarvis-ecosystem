import structlog
from app.core.event_bus import event_bus

logger = structlog.get_logger(__name__)

class MetricsAggregator:
    """Aggregates distributed node telemetry into centralized SaaS dashboards."""
    def __init__(self):
        self.metrics = {
            "total_renders": 0,
            "failed_renders": 0,
            "avg_render_duration": 0.0,
            "active_nodes": 0
        }
        event_bus.subscribe("WORKFLOW_COMPLETED", self._record_success)
        event_bus.subscribe("WORKFLOW_FAILED_PERMANENTLY", self._record_failure)
        event_bus.subscribe("WORKER_ONLINE", self._increment_nodes)
        event_bus.subscribe("WORKER_OFFLINE", self._decrement_nodes)

    async def _record_success(self, event: dict):
        self.metrics["total_renders"] += 1
        logger.info("metrics_updated_success", total=self.metrics["total_renders"])

    async def _record_failure(self, event: dict):
        self.metrics["failed_renders"] += 1
        logger.info("metrics_updated_failure", failures=self.metrics["failed_renders"])

    async def _increment_nodes(self, event: dict):
        self.metrics["active_nodes"] += 1
        
    async def _decrement_nodes(self, event: dict):
        self.metrics["active_nodes"] = max(0, self.metrics["active_nodes"] - 1)

metrics_aggregator = MetricsAggregator()
