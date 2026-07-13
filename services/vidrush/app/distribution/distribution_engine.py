import structlog
from app.core.event_bus import event_bus

logger = structlog.get_logger(__name__)

class DistributionEngine:
    def __init__(self):
        self.supported_platforms = ["youtube", "tiktok", "instagram_reels", "x_video"]

    async def schedule_deployment(self, video_path: str, metadata: dict, platforms: list):
        """
        Adapts the video and metadata for specific platforms and queues uploads.
        """
        for platform in platforms:
            if platform not in self.supported_platforms:
                continue
                
            logger.info("distribution_engine_adapting", platform=platform, video=video_path)
            
            # Platform specific adaptations
            adapted_metadata = self._adapt_metadata(metadata, platform)
            
            # Emit distribution payload to the upload_worker
            payload = {
                "platform": platform,
                "video_path": video_path,
                "metadata": adapted_metadata
            }
            await event_bus.publish("SYSTEM_UPLOAD_QUEUED", payload=payload)

    def _adapt_metadata(self, metadata: dict, platform: str) -> dict:
        """Modifies hashtags and titles based on the platform's algorithm rules."""
        adapted = metadata.copy()
        if platform == "tiktok":
            adapted["hashtags"] = metadata.get("hashtags", [])[:5] # TikTok prefers fewer tags
            adapted["title"] = metadata.get("title", "")[:100] # TikTok title limit
        elif platform == "youtube":
            adapted["hashtags"] = metadata.get("hashtags", [])[:15]
        return adapted

distribution_engine = DistributionEngine()
