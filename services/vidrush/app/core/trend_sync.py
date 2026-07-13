import structlog
from app.core.event_bus import event_bus

logger = structlog.get_logger(__name__)

class TrendSynchronizer:
    """Merges signals from Reddit, YouTube Analytics, and external trends to normalize priorities."""
    def __init__(self):
        event_bus.subscribe("EXTERNAL_REDDIT_STORY_FOUND", self._handle_reddit_signal)

    async def _handle_reddit_signal(self, event: dict):
        payload = event["payload"]
        score = payload.get("score", 0)
        
        # Normalization logic across different platform algorithms
        if score > 10000:
            normalized_score = min(int(score / 200), 100) # Convert upvotes to 0-100 priority
            logger.info("trend_sync_normalized_reddit", original_score=score, normalized=normalized_score)
            
            # Publish updated prioritization for the Scheduler
            await event_bus.publish("TREND_PRIORITY_UPDATE", payload={
                "topic": payload.get("title"),
                "source": "reddit",
                "score": normalized_score
            })

trend_sync = TrendSynchronizer()
