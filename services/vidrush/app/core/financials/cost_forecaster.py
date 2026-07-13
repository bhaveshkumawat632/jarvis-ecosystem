import structlog
from app.core.event_bus import event_bus

logger = structlog.get_logger(__name__)

class CostForecaster:
    """Predicts 'viral probability per infrastructure dollar' before execution."""
    def __init__(self):
        event_bus.subscribe("SYSTEM_TRIGGER_WORKFLOW", self.forecast_job_cost)

    async def forecast_job_cost(self, event: dict):
        task_id = event.get("task_id")
        topic = event["payload"].get("topic")
        
        # Predictive compute cost: (API tokens + GPU minutes + Storage)
        projected_cost = 0.25 # cents
        viral_probability = 0.85 # Mocked from predictive_optimizer
        
        roi_score = viral_probability / projected_cost
        
        logger.info("cost_forecaster_calculated", task_id=task_id, cost=projected_cost, roi=roi_score)
        
        if roi_score < 1.0:
            logger.warning("cost_forecast_warning_low_roi", task_id=task_id)
            await event_bus.publish("COST_FORECAST_WARNING", payload={"task_id": task_id, "roi": roi_score})
            # Scheduler might deprioritize this job

forecaster = CostForecaster()
