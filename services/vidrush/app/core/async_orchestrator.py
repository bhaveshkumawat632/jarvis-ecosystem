import asyncio
import structlog
from app.core.event_bus import event_bus
from app.core.task_state import task_state
from app.agents.director_agent import DirectorAgent
from app.agents.hook_agent import HookAgent
from app.agents.script_agent import ScriptAgent
from app.agents.emotion_agent import EmotionAgent
from app.agents.seo_agent import SEOAgent
from app.agents.thumbnail_agent import ThumbnailAgent
from app.visuals.visual_selector import VisualSelector

logger = structlog.get_logger(__name__)

class AsyncOrchestrator:
    def __init__(self):
        self.director = DirectorAgent()
        self.hook = HookAgent()
        self.script = ScriptAgent()
        self.emotion = EmotionAgent()
        self.seo = SEOAgent()
        self.thumbnail = ThumbnailAgent()
        self.visuals = VisualSelector()

    async def execute_workflow(self, topic: str, task_id: str):
        try:
            await task_state.update_state(task_id, "RUNNING")
            await event_bus.publish("WORKFLOW_STARTED", payload={"topic": topic}, task_id=task_id)

            # Phase 1: Director & Hook (Sequential dependency)
            direction = await asyncio.to_thread(self.director.direct, topic)
            hook_text = await asyncio.to_thread(self.hook.generate_hook, topic)
            await event_bus.publish("HOOK_READY", payload={"hook": hook_text}, task_id=task_id)

            # Phase 2: Agent Parallelization (Priority 8)
            # Run Script, SEO, Emotion, Thumbnail, Visuals concurrently!
            logger.info("orchestrator_parallelizing_agents", task_id=task_id)
            
            script_task = asyncio.to_thread(self.script.write_script, topic, hook_text)
            seo_task = asyncio.to_thread(self.seo.generate_seo_package, topic)
            emotion_task = asyncio.to_thread(self.emotion.analyze, hook_text)
            
            # Execute first batch of parallel agents
            full_script, seo_data, emotion_info = await asyncio.gather(script_task, seo_task, emotion_task)
            emotion_state = emotion_info.get("emotion", "neutral")
            
            await event_bus.publish("SCRIPT_READY", payload={"script": full_script}, task_id=task_id)

            # Second batch parallelization (Thumbnail & Visual Selector)
            thumb_task = asyncio.to_thread(self.thumbnail.generate_thumbnail, seo_data.get("title", topic), emotion_state)
            visuals_task = asyncio.to_thread(self.visuals.select_background, hook_text)
            
            thumb_path, (raw_bg, _) = await asyncio.gather(thumb_task, visuals_task)
            
            await event_bus.publish("VISUALS_READY", payload={"bg": raw_bg, "thumb": thumb_path}, task_id=task_id)
            
            # Future: Wait for Render Graph completion event here using event_bus
            await task_state.update_state(task_id, "COMPLETED")
            logger.info("workflow_execution_success", task_id=task_id)
            
        except Exception as e:
            logger.error("workflow_failsafe_recovery_triggered", task_id=task_id, error=str(e))
            await task_state.update_state(task_id, "FAILED", {"error": str(e)})
            await event_bus.publish("WORKFLOW_FAILED", payload={"error": str(e)}, task_id=task_id)
            # Priority 10: Retry mechanism can be hooked into the event bus listening to WORKFLOW_FAILED

async_orchestrator = AsyncOrchestrator()
