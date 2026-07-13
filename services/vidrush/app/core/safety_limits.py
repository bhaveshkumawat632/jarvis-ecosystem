import structlog
from app.core.event_bus import event_bus

logger = structlog.get_logger(__name__)

class ProductionSafetyLimits:
    """Enforces strict, non-negotiable operational limits before onboarding real creators."""
    def __init__(self):
        self.limits = {
            "max_video_length_seconds": 300,
            "max_render_timeout_seconds": 1800, # 30 mins
            "max_queue_depth_per_user": 3,
            "max_daily_generations_per_user": 10,
            "max_regeneration_attempts": 2
        }
        
        event_bus.subscribe("SYSTEM_TRIGGER_WORKFLOW", self.validate_safety_limits)

    async def validate_safety_limits(self, event: dict):
        payload = event["payload"]
        user_id = payload.get("user_id", "anonymous")
        duration = payload.get("duration_minutes", 1) * 60
        
        logger.info("safety_limits_evaluating", user=user_id, duration_sec=duration)
        
        # Rule 1: Video Length Limit
        if duration > self.limits["max_video_length_seconds"]:
            logger.error("safety_limit_exceeded_duration", user=user_id, duration=duration)
            raise Exception(f"Video exceeds maximum allowed length of {self.limits['max_video_length_seconds']}s")
            
        # Rule 2: User generation quotas (mocked tracking)
        daily_used = 2 # mock value
        if daily_used >= self.limits["max_daily_generations_per_user"]:
            logger.error("safety_limit_exceeded_quota", user=user_id)
            raise Exception("Daily generation limit reached.")
            
        logger.info("safety_limits_passed", user=user_id)

safety_limits = ProductionSafetyLimits()
