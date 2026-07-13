import structlog
from app.core.event_bus import event_bus

logger = structlog.get_logger(__name__)

class RetryPolicyEngine:
    """Centralized cluster decision maker for transient vs permanent failures."""
    def __init__(self):
        event_bus.subscribe("WORKFLOW_ERROR", self.evaluate_failure)

    async def evaluate_failure(self, event: dict):
        payload = event["payload"]
        error_msg = str(payload.get("error", "")).lower()
        task_id = event.get("task_id", "unknown")
        
        logger.info("retry_policy_evaluating", error=error_msg)
        
        # Transient network errors
        if "timeout" in error_msg or "rate limit" in error_msg or "429" in error_msg:
            logger.warning("transient_failure_detected_retrying", task_id=task_id)
            await event_bus.publish("SYSTEM_RETRY_WORKFLOW", payload={"task_id": task_id, "backoff": 60})
            
        # Permanent structural errors
        elif "missing before upload" in error_msg or "invalid format" in error_msg:
            logger.error("permanent_failure_detected_halting", task_id=task_id)
            await event_bus.publish("WORKFLOW_FAILED_PERMANENTLY", payload={"task_id": task_id, "reason": error_msg})

retry_policy = RetryPolicyEngine()
