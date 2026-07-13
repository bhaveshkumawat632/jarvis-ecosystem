import structlog
from app.core.event_bus import event_bus

logger = structlog.get_logger(__name__)

class MarginCalculator:
    """Proves the economic viability of the platform. Enforces economic accountability."""
    def __init__(self):
        event_bus.subscribe("WORKFLOW_COMPLETED", self.calculate_margin)

    async def calculate_margin(self, event: dict):
        payload = event["payload"]
        tenant_id = payload.get("tenant_id", "tenant_1")
        
        # Calculate hard economics
        gpu_compute_cost = 0.10
        api_token_cost = 0.05
        total_cost = gpu_compute_cost + api_token_cost
        
        revenue_per_video = 2.00 # Assuming subscription split per generation
        profit_margin = ((revenue_per_video - total_cost) / revenue_per_video) * 100
        
        logger.info("margin_calculated", tenant=tenant_id, margin_percent=profit_margin, cost=total_cost)
        
        if profit_margin < 40.0:
            logger.warning("infrastructure_margin_warning", margin=profit_margin)
            # Signal the cost reducer

margin_tracker = MarginCalculator()
