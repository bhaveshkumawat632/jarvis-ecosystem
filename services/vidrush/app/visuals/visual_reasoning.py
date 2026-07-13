import structlog

logger = structlog.get_logger(__name__)

class VisualReasoningEngine:
    def __init__(self):
        self.scene_memory = []

    def reason_visuals(self, script_context: str, emotion: str) -> dict:
        """
        Dynamically analyzes script chunks and maps to visual keywords.
        Example: "dark hallway" -> "horror footage"
        """
        logger.info("visual_reasoning_started", emotion=emotion)
        
        script_lower = script_context.lower()
        query = "abstract background loop"
        pacing = "medium"

        if "run" in script_lower or "chase" in script_lower or "panic" in script_lower:
            query = "car chase, running fast"
            pacing = "fast"
        elif emotion in ["fear", "tension"]:
            query = "dark scary creepy hallway"
            pacing = "slow"
        elif "minecraft" in script_lower or emotion == "neutral":
            query = "minecraft parkour gameplay"
        elif "sad" in script_lower or "crying" in script_lower:
            query = "rain window sad abstract"
            pacing = "slow"

        decision = {
            "search_query": query,
            "pacing": pacing,
            "requires_zoom": pacing == "fast",
            "darken_factor": 0.7 if emotion in ["fear", "tension"] else 0.4
        }
        
        self.scene_memory.append(decision)
        logger.info("visual_reasoning_completed", decision=decision)
        return decision

visual_reasoning = VisualReasoningEngine()
