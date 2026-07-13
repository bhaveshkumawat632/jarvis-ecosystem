import multiprocessing
import time
import structlog
from app.core.event_bus import event_bus

logger = structlog.get_logger(__name__)

class ProcessSupervisor:
    """Manages full lifecycle of isolated process workers. Enforces restarts and process isolation."""
    def __init__(self):
        self.managed_processes = {}
        self.max_retries = 3

    def spawn_worker(self, service_name: str, target_fn):
        """Spawns an isolated process for a specific media generation agent/worker."""
        process = multiprocessing.Process(target=target_fn, name=service_name, daemon=True)
        process.start()
        
        self.managed_processes[service_name] = {
            "process": process,
            "target": target_fn,
            "retries": 0,
            "start_time": time.time()
        }
        logger.info("supervisor_spawned_process", service=service_name, pid=process.pid)

    async def monitor_loop(self):
        """Continuously checks liveness of processes and recovers crashed ones."""
        logger.info("supervisor_monitoring_started")
        while True:
            for service, meta in list(self.managed_processes.items()):
                proc = meta["process"]
                if not proc.is_alive():
                    logger.warning("process_crashed", service=service, exitcode=proc.exitcode)
                    if meta["retries"] < self.max_retries:
                        meta["retries"] += 1
                        logger.info("supervisor_restarting_process", service=service, attempt=meta["retries"])
                        self.spawn_worker(service, meta["target"])
                    else:
                        logger.error("process_max_retries_exceeded", service=service)
                        await event_bus.publish("SYSTEM_CLUSTER_DEGRADED", payload={"failed_service": service})
            import asyncio
            await asyncio.sleep(5)

supervisor = ProcessSupervisor()
