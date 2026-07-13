import asyncio
import os
import edge_tts
import structlog
from abc import ABC, abstractmethod

logger = structlog.get_logger(__name__)

class BaseTTSEngine(ABC):
    @abstractmethod
    async def generate_audio(self, text: str, output_path: str, emotion: str = "neutral") -> str:
        pass

class EdgeTTSEngine(BaseTTSEngine):
    def __init__(self):
        self.presets = {
            "narrator_male": "en-US-ChristopherNeural",
            "narrator_female": "en-US-AriaNeural",
            "dramatic_male": "en-GB-RyanNeural"
        }

    def _get_emotion_params(self, emotion: str) -> dict:
        params = {"rate": "+0%", "pitch": "+0Hz"}
        if emotion in ["fear", "tension"]:
            params["rate"] = "-10%"
            params["pitch"] = "-5Hz"
        elif emotion == "excitement":
            params["rate"] = "+15%"
            params["pitch"] = "+5Hz"
        elif emotion == "sadness":
            params["rate"] = "-20%"
            params["pitch"] = "-15Hz"
        elif emotion == "betrayal":
            params["rate"] = "-15%"
            params["pitch"] = "-10Hz"
        elif emotion == "anger":
            params["rate"] = "+5%"
            params["pitch"] = "-20Hz"
        return params

    def _apply_text_prosody(self, text: str, emotion: str) -> str:
        # Lightweight text modulation to force EdgeTTS pauses/emphasis
        if emotion in ["sadness", "betrayal"]:
            text = text.replace(". ", "... ").replace(", ", "... ")
            text = text.replace(" found ", " found... ")
            text = text.replace(" opened ", " opened... ")
            text = text.replace(" lied ", " lied... ")
        elif emotion == "anger":
            text = text.replace(". ", "! ").replace(", ", "! ")
        return text

    async def generate_audio(self, text: str, output_path: str, emotion: str = "neutral", retries: int = 3) -> str:
        voice = self.presets["narrator_male"] # Default fallback
        params = self._get_emotion_params(emotion)
        text = self._apply_text_prosody(text, emotion)
        
        logger.info("tts_generation_started", emotion=emotion, rate=params["rate"], pitch=params["pitch"])

        for attempt in range(retries):
            try:
                communicate = edge_tts.Communicate(
                    text=text,
                    voice=voice,
                    rate=params["rate"],
                    pitch=params["pitch"]
                )
                await communicate.save(output_path)
                logger.info("tts_generation_completed", output_path=output_path)
                return output_path
            except Exception as e:
                logger.warning("tts_generation_failed", attempt=attempt+1, error=str(e))
                if attempt == retries - 1:
                    raise e
                await asyncio.sleep(2 ** attempt) # Exponential backoff
        return output_path

voice_generator = EdgeTTSEngine()
