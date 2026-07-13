import structlog
import traceback
import json
import os
from app.core.event_bus import event_bus

logger = structlog.get_logger(__name__)

class FailureCaptureSystem:
    """Saves complete environmental snapshots when workflows crash to save massive debugging time."""
    def __init__(self):
        self.crash_dir = "/home/junglee01/jarvis_universal/VidRush/outputs/crashes"
        os.makedirs(self.crash_dir, exist_ok=True)
        event_bus.subscribe("WORKFLOW_FAILED", self.capture_crash_state)

    async def capture_crash_state(self, event: dict):
        task_id = event["task_id"]
        error = event["payload"].get("error", "Unknown")
        original_event = event["payload"].get("original_event", {})
        
        crash_data = {
            "task_id": task_id,
            "error_message": error,
            "original_payload": original_event,
            "stacktrace": traceback.format_exc()
        }
        
        dump_path = os.path.join(self.crash_dir, f"crash_{task_id}.json")
        with open(dump_path, "w") as f:
            json.dump(crash_data, f, indent=2)
            
        logger.error("failure_snapshot_saved", path=dump_path, task_id=task_id)

failure_capture = FailureCaptureSystem()
