import structlog
from app.core.event_bus import event_bus

logger = structlog.get_logger(__name__)

class AutonomousCostController:
    """Estimates API and GPU power load costs to optimize ROI (viral potential per compute dollar)."""
    def __init__(self):
        self.budget_cap = 50.0 # Dollars per day
        self.spent_today = 0.0
        event_bus.subscribe("SYSTEM_TRIGGER_WORKFLOW", self.evaluate_cost)

    async def evaluate_cost(self, event: dict):
        task_id = event.get("task_id")
        topic = event["payload"].get("topic", "")
        
        # Cost logic: High API tokens + GPU Render
        estimated_job_cost = 0.15 
        
        if self.spent_today + estimated_job_cost > self.budget_cap:
            logger.error("cost_controller_threshold_exceeded", task_id=task_id, budget=self.budget_cap)
            await event_bus.publish("COST_THRESHOLD_EXCEEDED", payload={"task_id": task_id, "reason": "Budget cap reached"})
            raise Exception("Cost Threshold Exceeded")
            
        self.spent_today += estimated_job_cost
        logger.info("cost_controller_approved", task_id=task_id, spent=self.spent_today)

cost_controller = AutonomousCostController()
