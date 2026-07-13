import structlog
from abc import ABC, abstractmethod

logger = structlog.get_logger(__name__)

class AISceneGenerator(ABC):
    @abstractmethod
    async def generate_scene(self, prompt: str, emotion: str) -> str:
        """Provider-agnostic interface for visual generation."""
        pass

class ComfyUISceneGenerator(AISceneGenerator):
    async def generate_scene(self, prompt: str, emotion: str) -> str:
        # Future webhook implementation for ComfyUI / SDXL
        logger.info("ai_scene_generation_requested", provider="ComfyUI", prompt=prompt)
        return "temp/generated_scene_1.mp4"

class VisualGeneratorFabric:
    def __init__(self):
        self.providers = {
            "comfyui": ComfyUISceneGenerator()
        }

    async def get_visuals(self, script_context: str, emotion: str, provider: str = "comfyui") -> str:
        generator = self.providers.get(provider)
        if generator:
            logger.info("visual_fabric_routing", provider=provider)
            return await generator.generate_scene(script_context, emotion)
        return ""

scene_fabric = VisualGeneratorFabric()
