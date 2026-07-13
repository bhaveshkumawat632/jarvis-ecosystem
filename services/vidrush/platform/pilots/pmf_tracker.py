import structlog
from app.core.event_bus import event_bus

logger = structlog.get_logger(__name__)

class ProductMarketFitTracker:
    """Answers the ultimate question: Do creators actually want this?"""
    def __init__(self):
        event_bus.subscribe("HUMAN_FEEDBACK_RECEIVED", self.track_satisfaction)
        self.pilot_metrics = {"videos_generated": 0, "workflow_completion_rate": 0.0, "retention_rate": 0.0}

    async def track_satisfaction(self, event: dict):
        action = event["payload"].get("action")
        
        if action == "completed_export":
            self.pilot_metrics["videos_generated"] += 1
            logger.info("pmf_signal_positive_workflow_completed")
            
        # Mock calculation
        if self.pilot_metrics["videos_generated"] > 100:
            logger.info("pmf_validation_completed", metrics=self.pilot_metrics)
            await event_bus.publish("PMF_VALIDATION_COMPLETED", payload={"status": "confirmed"})

pmf_tracker = ProductMarketFitTracker()
