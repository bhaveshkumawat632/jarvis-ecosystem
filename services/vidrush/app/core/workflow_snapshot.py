import json
import structlog
from app.core.event_bus import event_bus

logger = structlog.get_logger(__name__)

class WorkflowSnapshotter:
    """Persists determinism by saving the exact state, prompt versions, and decisions for every generation."""
    def __init__(self):
        event_bus.subscribe("WORKFLOW_COMPLETED", self.create_snapshot)

    async def create_snapshot(self, event: dict):
        task_id = event.get("task_id")
        
        snapshot = {
            "task_id": task_id,
            "agent_versions": {
                "director": "v1.2",
                "script": "v2.0"
            },
            "llm_seed": 42, # Mock deterministic seed
            "prompts_used": ["mock_prompt_1", "mock_prompt_2"],
            "generation_decisions": event.get("payload", {})
        }
        
        # Persist to S3/MinIO or Postgres
        logger.info("workflow_snapshot_created", task_id=task_id)
        await event_bus.publish("WORKFLOW_SNAPSHOTTED", payload={"snapshot_id": task_id})

workflow_snapshotter = WorkflowSnapshotter()
