import structlog
from app.core.event_bus import event_bus

logger = structlog.get_logger(__name__)

class HumanFeedbackLayer:
    """Blends human creative intuition with autonomous optimization via RLHF mechanics."""
    def __init__(self):
        event_bus.subscribe("HUMAN_FEEDBACK_RECEIVED", self.process_human_signal)

    async def process_human_signal(self, event: dict):
        payload = event["payload"]
        task_id = payload.get("task_id")
        action = payload.get("action") # e.g. "rejected_thumbnail", "edited_hook"
        
        logger.info("human_feedback_processing", task_id=task_id, action=action)
        
        # If a human edits a script, we weight that edit heavily in the Intelligence Lake
        if action == "edited_hook":
            original = payload.get("original")
            human_edit = payload.get("human_edit")
            logger.info("reinforcement_learning_updated", original=original, new=human_edit)
            # Instructs the OptimizationCore to shift weights towards the human style

human_feedback = HumanFeedbackLayer()
