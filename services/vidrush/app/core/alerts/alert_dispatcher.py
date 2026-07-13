import structlog
from app.core.event_bus import event_bus

logger = structlog.get_logger(__name__)

class CriticalAlertDispatcher:
    """Routes high-severity infrastructure alerts directly to operator dashboards/pagers."""
    def __init__(self):
        self.critical_events = [
            "GPU_LIMIT_REACHED",
            "REDIS_CLUSTER_DEGRADED",
            "MASS_RENDER_FAILURE",
            "COST_MARGIN_COLLAPSE",
            "RETENTION_DROP_DETECTED",
            "API_ABUSE_DETECTED",
            "TENANT_ISOLATION_FAILURE"
        ]
        
        for event in self.critical_events:
            event_bus.subscribe(event, self.dispatch_pagerduty)

    async def dispatch_pagerduty(self, event: dict):
        # In a real environment, this triggers PagerDuty/Slack for SRE response
        logger.critical("OPERATOR_ALERT_DISPATCHED", alert_type=event.get("type"), payload=event.get("payload"))

alert_dispatcher = CriticalAlertDispatcher()
