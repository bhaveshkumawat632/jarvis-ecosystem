import structlog
from app.core.event_bus import event_bus

logger = structlog.get_logger(__name__)

class RenderClusterManager:
    def __init__(self):
        self.active_nodes = {}

    def register_node(self, node_id: str, gpu_info: dict):
        self.active_nodes[node_id] = {
            "status": "idle",
            "capabilities": gpu_info
        }
        logger.info("render_node_registered", node=node_id, gpus=gpu_info)

    async def dispatch_render_job(self, task_id: str, graph_data: dict):
        """
        Balances rendering workloads across registered remote GPU workers.
        """
        # Find idle node
        idle_nodes = [k for k, v in self.active_nodes.items() if v["status"] == "idle"]
        if not idle_nodes:
            logger.warning("no_idle_render_nodes", task_id=task_id)
            # Push to distributed queue for the next available worker
            await event_bus.publish("SYSTEM_RENDER_QUEUED", payload={"graph": graph_data, "task_id": task_id})
            return
            
        target_node = idle_nodes[0]
        self.active_nodes[target_node]["status"] = "rendering"
        logger.info("render_job_dispatched", node=target_node, task_id=task_id)
        
        # Publish event specifying the target node
        await event_bus.publish("SYSTEM_RENDER_ASSIGNED", payload={"node_id": target_node, "graph": graph_data, "task_id": task_id})

cluster_manager = RenderClusterManager()
