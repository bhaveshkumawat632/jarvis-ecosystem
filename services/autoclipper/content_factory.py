import os
import time
from datetime import datetime
import logging
import subprocess
import yt_dlp
import webvtt
import sys
import random

sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from memory.llm_gateway import LLMGateway
import config

os.environ["OLLAMA_API_KEY"] = config.OLLAMA_API_KEY
os.environ["LLM_PROVIDER"] = "ollama"

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class ContentFactory:
    def __init__(self):
        self.base_dir = os.path.dirname(os.path.abspath(__file__))
        self.ready_dir = os.path.join(self.base_dir, "shorts_factory", "ready_to_upload")
        self.history_file = os.path.join(self.base_dir, "shorts_factory", "factory_history.txt")
        os.makedirs(self.ready_dir, exist_ok=True)
        self.llm = LLMGateway()

    def is_processed(self, video_id: str) -> bool:
        if not os.path.exists(self.history_file): return False
        with open(self.history_file, 'r') as f:
            return video_id in f.read()

    def mark_processed(self, video_id: str):
        with open(self.history_file, 'a') as f:
            f.write(video_id + "\n")

    def download_video(self, url: str) -> dict:
        with yt_dlp.YoutubeDL({'quiet': True}) as ydl:
            info = ydl.extract_info(url, download=False)
            video_id = info['id']
            title = info.get('title', video_id)
            
        if self.is_processed(video_id):
            return None

        logger.info(f"[*] Factory Downloading {title}...")
        video_folder = os.path.join(self.base_dir, "shorts_factory", video_id)
        os.makedirs(video_folder, exist_ok=True)
        video_path = os.path.join(video_folder, "source.mp4")
        sub_path = os.path.join(video_folder, "subs.vtt")

        ydl_opts = {
            'format': 'bestvideo[ext=mp4][height<=1080]+bestaudio[ext=m4a]/best[ext=mp4]',
            'outtmpl': video_path,
            'writesubtitles': False,
            'writeautomaticsub': False,
            'subtitleslangs': ['en', 'hi', 'en-US'],
            'subtitlesformat': 'vtt',
            'quiet': False
        }

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])

        for f in os.listdir(video_folder):
            if f.endswith(".vtt"):
                os.rename(os.path.join(video_folder, f), sub_path)
                break

        return {"id": video_id, "folder": video_folder, "video_path": video_path, "sub_path": sub_path}

    def extract_5_viral_moments(self, sub_path: str) -> list:
        if not os.path.exists(sub_path):
            logger.warning("No subtitles found. Returning fallback moment.")
            return [{"start_time": "00:02:00", "end_time": "00:03:00", "reason": "Fallback funny moment"}]

        captions = []
        for caption in webvtt.read(sub_path):
            captions.append(f"[{caption.start}] {caption.text.replace(chr(10), ' ')}")
        
        transcript = "\n".join(captions[:400]) # Read a big chunk
        
        system_prompt = """You are a global viral content strategist. 
Analyze the transcript and find EXACTLY 5 highly visual, action-packed 45-60 second moments.
Return ONLY valid JSON array of objects:
[
  {"start_time": "00:01:10", "end_time": "00:02:00", "reason": "hook 1"},
  {"start_time": "00:03:00", "end_time": "00:03:50", "reason": "hook 2"}
]"""
        try:
            response = self.llm.execute_with_retry(system_prompt, f"Find 5 viral moments:\n\n{transcript}", max_retries=2)
            if isinstance(response, list) and len(response) <= 5:
                return response
        except Exception as e:
            logger.error(f"LLM Error: {e}")
            
        return [{"start_time": "00:00:30", "end_time": "00:01:20", "reason": "Fallback"}]

    def nvidia_qa_director(self, moment: dict, transcript: str) -> dict:
        """Forces NVIDIA API to QA check the clip and fix any bad cuts or boring content."""
        logger.info("Sending clip to NVIDIA QA Director for verification...")
        from memory.llm_gateway import OpenAILikeProvider
        
        qa_llm = LLMGateway()
        qa_llm.provider_type = "nim"
        base_url = "https://integrate.api.nvidia.com/v1"
        qa_llm.provider = OpenAILikeProvider(base_url, config.NIM_API_KEY, config.NIM_MODEL)
        
        system_prompt = """You are an elite YouTube Shorts Strategist. Your ONLY goal is 1 MILLION VIEWS minimum.
Review the proposed movie comedy clip based on the transcript.
Check for:
1. Mid-sentence cutoffs (fix timestamps if needed).
2. Is the hook insanely funny and engaging in the first 3 seconds?
3. Does this specific joke/scene have the potential to go viral and hit 1M views?
If it's weak, adjust the start_time and end_time slightly to capture the absolute peak punchline of the scene.
Return the fixed moment in EXACT JSON: {"start_time": "...", "end_time": "...", "reason": "...", "qa_approved": true}"""

        user_prompt = f"Proposed Clip: {moment}\nFull Transcript snippet:\n{transcript[:1000]}"
        
        try:
            response = qa_llm.execute_with_retry(system_prompt, user_prompt, max_retries=2)
            if isinstance(response, dict) and "qa_approved" in response:
                logger.info(f"NVIDIA QA Approved & Fixed: {response['reason']}")
                return response
        except Exception as e:
            logger.error(f"NVIDIA QA Error: {e}")
            
        return moment # Return original if QA fails

    def convert_to_seconds(self, time_str: str) -> float:
        if isinstance(time_str, (int, float)): return float(time_str)
        parts = time_str.split(':')
        if len(parts) == 3: return int(parts[0]) * 3600 + int(parts[1]) * 60 + float(parts[2])
        elif len(parts) == 2: return int(parts[0]) * 60 + float(parts[1])
        return float(time_str)

    def slice_and_polish(self, video_data: dict, moment: dict, index: int) -> str:
        """Applies 2026 Split-Screen Sensory Overload with Gameplay and AI Hook."""
        video_path = video_data['video_path']
        folder = video_data['folder']
        sub_path = video_data['sub_path']
        
        start_sec = self.convert_to_seconds(moment.get('start_time', moment.get('start')))
        end_sec = self.convert_to_seconds(moment.get('end_time', moment.get('end')))
        duration = end_sec - start_sec
        
        timestamp = int(time.time())
        output_filename = f"brainrot_{video_data['id']}_part{index}_{timestamp}.mp4"
        output_path = os.path.join(self.ready_dir, output_filename)
        
        gameplay_path = os.path.join(self.base_dir, "assets", "gameplay.mp4")
        hook_path = os.path.join(self.base_dir, "assets", "hook.mp3")
        
        sub_time_start = max(0, duration - 3)
        
        # Scavenger Hunt Trap Logic
        emoji_start = random.uniform(2.0, max(2.1, duration - 5.0))
        emoji_end = emoji_start + 0.8  # Flashes for exactly 0.8 seconds
        emoji_x = random.randint(50, 950)
        emoji_y = random.randint(150, 1400)
        
        # 2026 FOOLPROOF BPR (Brainrot, Padding, Retention) MATRIX
        sub_filter = f"[v_stacked]subtitles='{sub_path}':force_style='FontSize=20,Alignment=2,MarginV=420,PrimaryColour=&H0000FFFF,OutlineColour=&H00000000,BorderStyle=1,Outline=2'[v_subbed];" if os.path.exists(sub_path) else "[v_stacked]format=yuv420p[v_subbed];"
        
        visual_filter = (
            "[0:v]setpts=0.95*PTS,hflip,scale=1080:1536:force_original_aspect_ratio=increase,crop=1080:1536,noise=c0s=2:c0f=t+u[v_top];"
            "[1:v]scale=1080:384:force_original_aspect_ratio=increase,crop=1080:384[v_bot];"
            "[v_top][v_bot]vstack=inputs=2[v_stacked];"
            f"{sub_filter}"
            f"[v_subbed]drawtext=text='I hid a 👽 emoji! 99% fail to find it!':fontcolor=yellow:fontsize=45:x=(w-text_w)/2:y=80:box=1:boxcolor=black@0.6:boxborderw=10[v_text1];"
            f"[v_text1]drawtext=text='👽':fontsize=35:x={emoji_x}:y={emoji_y}:alpha=0.6:enable='between(t,{emoji_start},{emoji_end})'[v_text2];"
            f"[v_text2]drawtext=text='SUBSCRIBE IF YOU LAUGHED! 👇':fontcolor=white:fontsize=50:x=(w-text_w)/2:y=1300:box=1:boxcolor=red@0.8:boxborderw=10:enable='between(t,{sub_time_start},{duration})'[v_final]"
        )
        
        audio_filter = (
            "[0:a]volume=1.0[a_movie];"
            "[2:a]volume=1.5,adelay=0|0[a_hook];"
            "[a_movie][a_hook]amix=inputs=2:duration=first:dropout_transition=0[a_mixed];"
            "[a_mixed]asetrate=48000,aresample=44100[a_final]"
        )

        cmd = [
            'ffmpeg', '-y', 
            '-ss', str(start_sec), 
            '-i', video_path,
            '-stream_loop', '-1', '-i', gameplay_path,
            '-i', hook_path,
            '-t', str(duration),
            '-filter_complex', f"{visual_filter};{audio_filter}",
            '-map', '[v_final]',
            '-map', '[a_final]',
            '-c:v', 'libx264',
            '-c:a', 'aac',
            output_path
        ]
        
        logger.info(f"[*] Rendering 2026 Split-Screen Brainrot Short {index} ({duration}s)...")
        subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        
        return output_path if os.path.exists(output_path) else None

    def run_factory(self):
        NICHES = [
            "ytsearch5:Old Bollywood comedy movie scene hd",
            "ytsearch5:Hera Pheri best comedy scenes",
            "ytsearch5:Welcome movie comedy scene",
            "ytsearch5:Old Hollywood comedy movie scenes hd",
            "ytsearch5:Phir Hera Pheri epic comedy",
            "ytsearch5:Dhamaal movie best comedy scenes"
        ]
        selected_niche = random.choice(NICHES)
        logger.info(f"Factory waking up! Automatically searching for movie comedy niche: {selected_niche}")
        
        urls = []
        try:
            with yt_dlp.YoutubeDL({'quiet': True, 'extract_flat': True}) as ydl:
                info = ydl.extract_info(selected_niche, download=False)
                urls = [entry['url'] for entry in info.get('entries', [])]
        except Exception as e:
            logger.error(f"Search failed: {e}")
            return
            
        if not urls:
            logger.warning("No videos found in search.")
            return

        for url in urls:
            # Enforce working hours (2 AM to 10 AM)
            current_hour = datetime.now().hour
            if not (2 <= current_hour < 10):
                logger.info("Outside working hours (2 AM - 10 AM). Factory shutting down.")
                break
                
            video_data = self.download_video(url)
            if not video_data: continue
                
            moments = self.extract_5_viral_moments(video_data['sub_path'])
            
            # Load transcript once for QA
            transcript_text = ""
            if os.path.exists(video_data['sub_path']):
                transcript_text = "\n".join([f"[{c.start}] {c.text}" for c in webvtt.read(video_data['sub_path'])[:200]])

            for i, moment in enumerate(moments):
                if not (2 <= datetime.now().hour < 10):
                    break
                
                # 1. NVIDIA QA VERIFICATION LAYER
                verified_moment = self.nvidia_qa_director(moment, transcript_text)
                
                # 2. FINAL POLISH RENDER
                self.slice_and_polish(video_data, verified_moment, i+1)
                
            self.mark_processed(video_data['id'])
            
            # Clean up massive source file
            if os.path.exists(video_data['video_path']):
                os.remove(video_data['video_path'])

if __name__ == "__main__":
    logger.info("Factory Started...")
    factory = ContentFactory()
    factory.run_factory()
