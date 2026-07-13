import os
from configs.settings import TEMP_DIR, OUTPUT_DIR
from app.agents.director_agent import DirectorAgent
from app.agents.hook_agent import HookAgent
from app.agents.script_agent import ScriptAgent
from app.agents.emotion_agent import EmotionAgent
from app.agents.seo_agent import SEOAgent
from app.agents.thumbnail_agent import ThumbnailAgent
from app.visuals.visual_selector import VisualSelector
from app.visuals.loop_engine import LoopEngine
from app.subtitles.subtitle_engine import SubtitleEngine
from app.rendering.ffmpeg_renderer import FFmpegRenderer
from app.core.memory_system import MemorySystem
from app.core.analytics_engine import AnalyticsEngine

class Orchestrator:
    def __init__(self):
        self.director = DirectorAgent()
        self.hook = HookAgent()
        self.script = ScriptAgent()
        self.emotion = EmotionAgent()
        self.seo = SEOAgent()
        self.thumbnail = ThumbnailAgent()
        self.visuals = VisualSelector()
        self.loop = LoopEngine()
        self.subtitles = SubtitleEngine()
        self.renderer = FFmpegRenderer()
        self.memory = MemorySystem()
        self.analytics = AnalyticsEngine()

    def run_full_pipeline(self, topic: str, duration: int, quality: str, task_updater=None):
        def update_progress(progress, stage):
            if task_updater:
                try:
                    task_updater(state='PROGRESS', meta={'progress': progress, 'stage': stage})
                except Exception as e:
                    print(f"Failed to update progress: {e}")

        print(f"=== Starting VidRush Pipeline: {topic} ===")
        update_progress(10, 'Generating Script...')
        
        # 1. Director decides style
        direction = self.director.direct(topic)
        print("Direction:", direction)
        
        # 2. Hook & Script
        hook_text = self.hook.generate_hook(topic)
        self.memory.store_pattern(hook_text, topic, direction.get("style", "reddit"), 1.0)
        full_script = self.script.write_script(topic, hook_text)
        print("Script generated.")
        update_progress(25, 'Processing audio and visuals...')
        
        # 3. Emotion Detection
        emotion_info = self.emotion.analyze(hook_text)
        emotion_state = emotion_info.get("emotion", "neutral")
        
        # 4. SEO & Thumbnail
        seo_data = self.seo.generate_seo_package(topic)
        thumb_path = self.thumbnail.generate_thumbnail(seo_data.get("title", topic), emotion_state)
        print(f"SEO and Thumbnail ready: {thumb_path}")
        # 5. Audio (True TTS generation using edge-tts)
        audio_path = os.path.join(TEMP_DIR, "narration.mp3")
        import subprocess
        print("Generating TTS audio via edge-tts...")
        subprocess.run(["edge-tts", "--voice", "en-US-ChristopherNeural", "--text", full_script, "--write-media", audio_path], check=True, stdout=subprocess.DEVNULL)
        
        # Get actual audio duration
        ffprobe_cmd = ["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "default=noprint_wrappers=1:nokey=1", audio_path]
        try:
            actual_duration = float(subprocess.check_output(ffprobe_cmd).decode('utf-8').strip())
            # Cap at 120s to keep render times reasonable
            actual_duration = min(actual_duration, 120.0)
            print(f"TTS Audio Duration: {actual_duration}s (capped). Overriding requested duration ({duration}s).")
            duration = actual_duration
        except:
            print("Failed to probe audio duration, using requested duration.")

        update_progress(50, 'Rendering visuals...')
        
        # 6. Visuals & Looping
        raw_bg, _ = self.visuals.select_background(topic, hook_text)
        processed_bg = os.path.join(TEMP_DIR, "processed_bg.mp4")
        self.loop.process(raw_bg, duration, processed_bg)
        
        update_progress(75, 'Generating subtitles...')
        
        # 7. Subtitles
        ass_path = os.path.join(TEMP_DIR, "subs.ass")
        self.subtitles.generate_ass(audio_path, ass_path, emotion_state)
        update_progress(90, 'Finalizing render...')
        
        # 8. Render — keep filename short (ext4 limit = 255 chars)
        import re, hashlib
        safe_topic = re.sub(r'[^a-zA-Z0-9]+', '_', topic)[:30].strip('_')
        short_hash = hashlib.md5(topic.encode()).hexdigest()[:8]
        final_output = os.path.join(OUTPUT_DIR, f"{safe_topic}_{short_hash}_{quality}.mp4")
        self.renderer.render(processed_bg, audio_path, None, ass_path, final_output)
        
        print(f"=== Pipeline Complete! Saved to {final_output} ===")
        update_progress(100, 'COMPLETED')
        return final_output

if __name__ == "__main__":
    orch = Orchestrator()
    orch.run_full_pipeline("I Found My Wife Secret Life", 1, "1080p")
