import json
import os
import structlog
import redis.asyncio as redis
from configs.settings import BASE_DIR, REDIS_URL

logger = structlog.get_logger(__name__)

class TaskStateManager:
    def __init__(self):
        self.fallback_file = os.path.join(BASE_DIR, "logs", "task_state.json")
        self.redis_client = None
        
    async def connect(self):
        try:
            self.redis_client = await redis.from_url(REDIS_URL, decode_responses=True)
            await self.redis_client.ping()
            logger.info("state_manager_connected_redis")
        except Exception as e:
            logger.warning("redis_connection_failed_using_json_fallback", error=str(e))
            print(f"REDIS FALLBACK REASON: {e}")
            import traceback
            traceback.print_exc()
            self.redis_client = None
            if not os.path.exists(self.fallback_file):
                os.makedirs(os.path.dirname(self.fallback_file), exist_ok=True)
                with open(self.fallback_file, "w") as f:
                    json.dump({}, f)

    async def update_state(self, task_id: str, state: str, metadata: dict = None):
        valid_states = {"PENDING", "RUNNING", "FAILED", "RETRYING", "COMPLETED"}
        if state not in valid_states:
            raise ValueError(f"Invalid state: {state}")
            
        data = {
            "state": state,
            "metadata": metadata or {}
        }
        
        if self.redis_client:
            await self.redis_client.set(f"task:{task_id}", json.dumps(data))
        else:
            with open(self.fallback_file, "r") as f:
                fallback_data = json.load(f)
            fallback_data[task_id] = data
            with open(self.fallback_file, "w") as f:
                json.dump(fallback_data, f, indent=4)
                
        logger.info("task_state_updated", task_id=task_id, state=state)

    async def get_state(self, task_id: str):
        if self.redis_client:
            data = await self.redis_client.get(f"task:{task_id}")
            return json.loads(data) if data else None
        else:
            if not os.path.exists(self.fallback_file):
                return None
            with open(self.fallback_file, "r") as f:
                fallback_data = json.load(f)
            return fallback_data.get(task_id)

task_state = TaskStateManager()
