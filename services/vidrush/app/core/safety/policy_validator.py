import structlog
from app.core.event_bus import event_bus

logger = structlog.get_logger(__name__)

class SafetyConstraintEngine:
    """MANDATORY: Prevents unsafe outputs, platform violations, and spam generation."""
    def __init__(self):
        event_bus.subscribe("SYSTEM_UPLOAD_QUEUED", self.validate_safety)

    async def validate_safety(self, event: dict):
        payload = event["payload"]
        metadata = payload.get("metadata", {})
        task_id = payload.get("task_id", "unknown")
        
        logger.info("safety_engine_evaluating", task_id=task_id)
        
        restricted_keywords = ["violence", "nsfw", "hack", "illegal"]
        title_lower = metadata.get("title", "").lower()
        
        for word in restricted_keywords:
            if word in title_lower:
                logger.error("safety_review_failed", task_id=task_id, word=word)
                await event_bus.publish("SAFETY_REVIEW_FAILED", payload={
                    "task_id": task_id,
                    "reason": f"Platform violation: detected restricted term '{word}'"
                })
                raise Exception("Safety Constraint Violated")
                
        logger.info("safety_engine_approved", task_id=task_id)

safety_engine = SafetyConstraintEngine()
