import os
import asyncio
import structlog
from faster_whisper import WhisperModel

logger = structlog.get_logger(__name__)

def format_time(seconds):
    h = int(seconds // 3600)
    m = int((seconds % 3600) // 60)
    s = seconds % 60
    return f"{h}:{m:02d}:{s:05.2f}"

class SubtitlePipeline:
    def __init__(self, model_size="small.en", device="cuda"):
        try:
            self.model = WhisperModel(model_size, device=device, compute_type="float16")
            logger.info("whisper_model_loaded", device=device)
        except Exception as e:
            logger.warning("whisper_cuda_failed_fallback_cpu", error=str(e))
            self.model = WhisperModel(model_size, device="cpu", compute_type="int8")

    def _get_emotion_style(self, emotion: str):
        color_map = {
            "fear": ("&H000000FF&", "😱"),    # Red
            "tension": ("&H000000FF&", "😨"), # Red
            "sadness": ("&H00FF0000&", "😢"), # Blue
            "excitement": ("&H0000FFFF&", "🔥"), # Yellow
            "neutral": ("&H00FFFFFF&", "")     # White
        }
        return color_map.get(emotion, ("&H00FFFFFF&", ""))

    async def generate_subtitles(self, audio_path: str, output_ass: str, emotion: str = "neutral"):
        logger.info("subtitle_generation_started", audio_path=audio_path)
        
        # CPU bound task, offload to thread
        segments, _ = await asyncio.to_thread(self.model.transcribe, audio_path, word_timestamps=True)
        
        primary_color, emoji = self._get_emotion_style(emotion)
        
        ass_header = f"""[Script Info]
ScriptType: v4.00+
PlayResX: 1920
PlayResY: 1080

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Default,Arial,120,&H00FFFFFF&,&H000000FF,&H00000000,&HA0000000,-1,0,0,0,95,95,2,0,1,8,2,5,150,150,500,1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""
        with open(output_ass, "w", encoding="utf-8") as f:
            f.write(ass_header)
            
            for segment in segments:
                words = segment.words
                chunk_size = 4
                for i in range(0, len(words), chunk_size):
                    chunk = words[i:i+chunk_size]
                    start = format_time(chunk[0].start)
                    end = format_time(chunk[-1].end)
                    text = " ".join([w.word.strip() for w in chunk])
                    
                    # Subtle kinetic typography pop for phrases
                    dialogue = f"Dialogue: 0,{start},{end},Default,,0,0,0,,{{\\fscx110\\fscy110\\t(0,150,\\fscx100\\fscy100)}}{text} {emoji}\n"
                    f.write(dialogue)
        
        logger.info("subtitle_generation_completed", output_path=output_ass)
        return output_ass

subtitle_pipeline = SubtitlePipeline()
