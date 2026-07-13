import asyncio
import structlog
from app.core.event_bus import event_bus
from app.core.gpu_manager import gpu_manager

logger = structlog.get_logger(__name__)

class AIProductionScheduler:
    def __init__(self):
        self.queue = []
        self._running = False

    async def schedule_video(self, topic: str, priority_score: int):
        """Intelligently queues videos based on trend timing and priority."""
        self.queue.append({"topic": topic, "score": priority_score})
        self.queue.sort(key=lambda x: x["score"], reverse=True)
        logger.info("scheduler_video_queued", topic=topic, score=priority_score)

    async def run_loop(self):
        self._running = True
        logger.info("ai_scheduler_started")
        
        while self._running:
            if not self.queue:
                await asyncio.sleep(10)
                continue
                
            # Detect idle GPU windows
            gpu_usage = gpu_manager.get_vram_usage()
            is_idle = False
            
            if gpu_usage.get("status") == "no_gpu":
                is_idle = True # CPU fallback mode
            elif gpu_usage.get("status") != "error":
                if gpu_usage.get("percent", 100) < 30.0:
                    is_idle = True
                    
            if is_idle and self.queue:
                next_job = self.queue.pop(0)
                logger.info("scheduler_dispatching_job", topic=next_job["topic"])
                # Dispatch the job via Event Bus
                await event_bus.publish("SYSTEM_TRIGGER_WORKFLOW", payload={"topic": next_job["topic"]})
                
            await asyncio.sleep(15) # Polling interval

ai_scheduler = AIProductionScheduler()
