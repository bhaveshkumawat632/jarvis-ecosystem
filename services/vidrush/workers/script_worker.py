import asyncio
import structlog
from app.core.event_bus import event_bus
from app.agents.script_agent import ScriptAgent
from app.agents.hook_agent import HookAgent
from app.agents.director_agent import DirectorAgent

logger = structlog.get_logger(__name__)

class ScriptWorker:
    def __init__(self):
        self.director = DirectorAgent()
        self.hook = HookAgent()
        self.script = ScriptAgent()
        # Subscribe to workflow trigger to begin the pipeline
        event_bus.subscribe("SYSTEM_TRIGGER_WORKFLOW", self.process_request)

    async def process_request(self, event: dict):
        task_id = event["task_id"]
        payload = event["payload"]
        topic = payload.get("topic")
        
        logger.info("script_worker_started", task_id=task_id, topic=topic)
        try:
            await event_bus.publish("WORKFLOW_STARTED", payload={"topic": topic}, task_id=task_id)

            # Phase 1: Direction & Hook
            direction = await asyncio.to_thread(self.director.direct, topic)
            hook_text = await asyncio.to_thread(self.hook.generate_hook, topic)
            
            await event_bus.publish("HOOK_READY", payload={"hook": hook_text, "direction": direction}, task_id=task_id)

            # Phase 2: Full Script
            full_script = await asyncio.to_thread(self.script.write_script, topic, hook_text)
            
            await event_bus.publish("SCRIPT_READY", payload={"script": full_script, "hook": hook_text, "direction": direction}, task_id=task_id)
            logger.info("script_worker_completed", task_id=task_id)
            
        except Exception as e:
            logger.error("script_worker_failed", task_id=task_id, error=str(e))
            await event_bus.publish("WORKFLOW_FAILED", payload={"error": str(e), "worker": "ScriptWorker"}, task_id=task_id)

script_worker = ScriptWorker()
