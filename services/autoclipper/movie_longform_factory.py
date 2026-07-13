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

logging.basicConfig(level=logging.INFO, format='%(asctime)s - [LONGFORM FACTORY] - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class MovieLongformFactory:
    def __init__(self):
        self.base_dir = os.path.dirname(os.path.abspath(__file__))
        self.ready_dir = os.path.join(self.base_dir, "longform_factory", "ready_to_upload")
        self.history_file = os.path.join(self.base_dir, "longform_factory", "movie_history.txt")
        os.makedirs(self.ready_dir, exist_ok=True)
        self.llm = LLMGateway()

    def is_processed(self, video_id: str) -> bool:
        if not os.path.exists(self.history_file): return False
        with open(self.history_file, 'r') as f:
            return video_id in f.read()

    def mark_processed(self, video_id: str):
        with open(self.history_file, 'a') as f:
            f.write(video_id + "\n")

    def download_movie(self, url: str) -> dict:
        with yt_dlp.YoutubeDL({'quiet': True}) as ydl:
            info = ydl.extract_info(url, download=False)
            video_id = info['id']
            title = info.get('title', video_id)
            
        if self.is_processed(video_id):
            return None

        logger.info(f"[*] Factory Downloading Movie: {title}...")
        video_folder = os.path.join(self.base_dir, "longform_factory", video_id)
        os.makedirs(video_folder, exist_ok=True)
        video_path = os.path.join(video_folder, "source.mp4")
        sub_path = os.path.join(video_folder, "subs.vtt")

        ydl_opts = {
            'format': 'bestvideo[ext=mp4][height<=1080]+bestaudio[ext=m4a]/best[ext=mp4]',
            'outtmpl': video_path,
            'quiet': False
        }

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])

        for f in os.listdir(video_folder):
            if f.endswith(".vtt"):
                os.rename(os.path.join(video_folder, f), sub_path)
                break

        return {"id": video_id, "folder": video_folder, "video_path": video_path, "sub_path": sub_path}

    def extract_epic_movie_scene(self, sub_path: str) -> dict:
        if not os.path.exists(sub_path):
            return {"start_time": "00:10:00", "end_time": "00:15:00", "reason": "Fallback scene"}

        captions = []
        for caption in webvtt.read(sub_path):
            captions.append(f"[{caption.start}] {caption.text.replace(chr(10), ' ')}")
        
        # Read a massive chunk for a full movie
        transcript = "\n".join(captions[:2000])
        
        system_prompt = """You are an elite Movie Review Channel Director. Your goal is 1 MILLION VIEWS minimum.
Analyze the movie transcript and find exactly ONE continuous, incredibly funny and epic scene sequence lasting between 3 to 6 minutes.
This will become a "Short Movie".
Return ONLY valid JSON:
{"start_time": "00:15:30", "end_time": "00:20:45", "reason": "Babu Rao epic fight scene"}"""
        
        try:
            response = self.llm.execute_with_retry(system_prompt, f"Find the best 5-minute comedy scene:\n\n{transcript}", max_retries=2)
            if isinstance(response, dict) and "start_time" in response:
                return response
        except Exception as e:
            logger.error(f"LLM Error: {e}")
            
        return {"start_time": "00:10:00", "end_time": "00:15:00", "reason": "Fallback scene"}

    def nvidia_qa_director_longform(self, moment: dict, transcript: str) -> dict:
        logger.info("Sending longform scene to NVIDIA QA Director for verification...")
        from memory.llm_gateway import OpenAILikeProvider
        
        qa_llm = LLMGateway()
        qa_llm.provider_type = "nim"
        base_url = "https://integrate.api.nvidia.com/v1"
        qa_llm.provider = OpenAILikeProvider(base_url, config.NIM_API_KEY, config.NIM_MODEL)
        
        system_prompt = """You are a rigorous QA Director. Review the proposed 5-minute movie scene.
Ensure it doesn't cut off mid-dialogue at the start or end. If it does, adjust the start_time/end_time by a few seconds.
Ensure it is a highly engaging, continuous funny sequence.
Return exact JSON: {"start_time": "...", "end_time": "...", "reason": "...", "qa_approved": true}"""

        user_prompt = f"Proposed Scene: {moment}\nTranscript:\n{transcript[:2000]}"
        
        try:
            response = qa_llm.execute_with_retry(system_prompt, user_prompt, max_retries=2)
            if isinstance(response, dict) and "qa_approved" in response:
                logger.info(f"NVIDIA QA Approved Longform: {response['reason']}")
                return response
        except Exception as e:
            logger.error(f"NVIDIA QA Error: {e}")
            
        return moment

    def convert_to_seconds(self, time_str: str) -> float:
        if isinstance(time_str, (int, float)): return float(time_str)
        parts = time_str.split(':')
        if len(parts) == 3: return int(parts[0]) * 3600 + int(parts[1]) * 60 + float(parts[2])
        elif len(parts) == 2: return int(parts[0]) * 60 + float(parts[1])
        return float(time_str)

    def render_short_movie(self, video_data: dict, moment: dict) -> str:
        """Applies 16:9 copyright bypass and circular Brainrot Gameplay overlay."""
        video_path = video_data['video_path']
        folder = video_data['folder']
        sub_path = video_data['sub_path']
        
        start_sec = self.convert_to_seconds(moment.get('start_time', moment.get('start')))
        end_sec = self.convert_to_seconds(moment.get('end_time', moment.get('end')))
        duration = end_sec - start_sec
        
        timestamp = int(time.time())
        output_filename = f"shortmovie_{video_data['id']}_{timestamp}.mp4"
        output_path = os.path.join(self.ready_dir, output_filename)
        gameplay_path = os.path.join(os.path.dirname(self.base_dir), "autoclipper", "assets", "gameplay.mp4")
        
        # Level 9 Bypass (Virtual Cinema + Cam-Wobble)
        visual_filter = (
            "[0:v]setpts=0.92*PTS,crop=iw*0.95:ih*0.95,scale=1920:1080,eq=saturation=1.2:contrast=1.1:brightness=0.02,rotate='0.02*sin(t*2)':ow=iw:oh=ih:c=black,noise=c0s=4:c0f=t+u[bg];"
            "[1:v]scale=300:300:force_original_aspect_ratio=increase,crop=300:300,format=yuva420p,"
            "geq=lum='p(X,Y)':a='if(lt((X-W/2)*(X-W/2)+(Y-H/2)*(Y-H/2),150*150),255,0)'[game_circle];"
            "[bg][game_circle]overlay=W-w-50:50[v]"
        )
        audio_filter = (
            "[0:a]asetrate=48000,aresample=44100,volume=1.0[main_audio];"
            "[2:a]volume=0.3[lofi_audio];"
            "[main_audio][lofi_audio]amix=inputs=2:duration=first:dropout_transition=0[a]"
        )

        cmd = [
            'ffmpeg', '-y', 
            '-ss', str(start_sec), 
            '-i', video_path,
            '-stream_loop', '-1', '-i', gameplay_path,
            '-stream_loop', '-1', '-i', os.path.join(os.path.dirname(self.base_dir), "autoclipper", "assets", "lofi.mp3"),
            '-t', str(duration),
            '-filter_complex', f"{visual_filter};{audio_filter}",
            '-map', '[v]',
            '-map', '[a]',
            '-c:v', 'libx264',
            '-c:a', 'aac',
            output_path
        ]
        
        logger.info(f"[*] Rendering Longform Short Movie ({duration}s)...")
        subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        
        return output_path if os.path.exists(output_path) else None

    def run_factory(self):
        NICHES = [
            "ytsearch2:Old Bollywood comedy full movie hd",
            "ytsearch2:Hera Pheri full movie",
            "ytsearch2:Welcome full movie comedy",
            "ytsearch2:Dhamaal full movie hd"
        ]
        selected_niche = random.choice(NICHES)
        logger.info(f"Longform Factory waking up! Searching for: {selected_niche}")
        
        urls = []
        try:
            with yt_dlp.YoutubeDL({'quiet': True, 'extract_flat': True}) as ydl:
                info = ydl.extract_info(selected_niche, download=False)
                urls = [entry['url'] for entry in info.get('entries', [])][:1] # Just 1 movie a day is enough for 1 longform
        except Exception as e:
            logger.error(f"Search failed: {e}")
            return

        for url in urls:
            current_hour = datetime.now().hour
            # if not (2 <= current_hour < 10):
            #     logger.info("Outside working hours (2 AM - 10 AM). Factory shutting down.")
            #     break
                
            video_data = self.download_movie(url)
            if not video_data: continue
                
            moment = self.extract_epic_movie_scene(video_data['sub_path'])
            
            transcript_text = ""
            if os.path.exists(video_data['sub_path']):
                transcript_text = "\n".join([f"[{c.start}] {c.text}" for c in webvtt.read(video_data['sub_path'])[:2000]])

            verified_moment = self.nvidia_qa_director_longform(moment, transcript_text)
            self.render_short_movie(video_data, verified_moment)
            self.mark_processed(video_data['id'])
            
            if os.path.exists(video_data['video_path']):
                os.remove(video_data['video_path'])

if __name__ == "__main__":
    logger.info("Longform Movie Factory Started...")
    factory = MovieLongformFactory()
    factory.run_factory()
