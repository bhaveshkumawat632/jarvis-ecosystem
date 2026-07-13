import structlog
from app.core.event_bus import event_bus

logger = structlog.get_logger(__name__)

class BaseConnector:
    def __init__(self, platform_name: str):
        self.platform = platform_name

    async def fetch_and_publish(self):
        """Must be implemented by subclasses to fetch data and emit INTELLIGENCE_GATHERED events."""
        raise NotImplementedError

    async def publish_intel(self, payload: dict):
        event_payload = {
            "platform": self.platform,
            "data": payload
        }
        await event_bus.publish("EXTERNAL_INTELLIGENCE_GATHERED", payload=event_payload)
        logger.info("external_intel_published", platform=self.platform)
