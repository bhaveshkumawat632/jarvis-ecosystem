import os
import re
import json
import random
import subprocess
import requests
import math
import sys
from datetime import datetime

sys.path.append("/home/junglee01/jarvis_ecosystem/services/autoclipper")
from youtube_uploader import YouTubeUploader

class RedditShortsFactory:
    def __init__(self):
        self.base_dir = "/home/junglee01/jarvis_ecosystem/services/reddit_shorts"
        self.assets_dir = os.path.join(self.base_dir, "assets")
        self.output_dir = os.path.join(self.base_dir, "output")
        os.makedirs(self.assets_dir, exist_ok=True)
        os.makedirs(self.output_dir, exist_ok=True)
        
        self.gameplay_vid = os.path.join(self.assets_dir, "gameplay.mp4")
        self.bgm_audio = os.path.join(self.assets_dir, "bgm.mp3")

    def fetch_reddit_story(self):
        print("[*] Fetching viral story from local database...")
        stories = [
            "My brother has been hiding a secret for 10 years, and today I found out what it is. I was cleaning out the attic when I found an old locked box. I pried it open and inside were letters from a woman claiming to be his real mother. He had no idea, and now I don't know if I should tell him.",
            "I accidentally ruined my best friend's wedding and I feel terrible. I was responsible for the cake, but I tripped and dropped it right as she was walking into the reception. Everyone stared at me, and she ran out crying. I don't know how to fix this.",
            "I found out my boss is embezzling money, and he offered me a promotion to keep quiet. If I report him, the company might go under and we all lose our jobs. But if I take the promotion, I become an accomplice. I am absolutely terrified of making the wrong choice."
        ]
        text = random.choice(stories)
        return text

    def generate_audio(self, text, output_path):
        print("[*] Generating Fast-Paced TTS via Edge-TTS...")
        # Escape quotes
        safe_text = text.replace('"', '\\"').replace("'", "\\'")
        # Increased speed by 15% for higher retention
        cmd = ['edge-tts', '--voice', 'en-US-ChristopherNeural', '--rate', '+15%', '--text', text, '--write-media', output_path]
        subprocess.run(cmd, check=True)

    def get_audio_duration(self, audio_path):
        cmd = [
            'ffprobe', '-v', 'error', '-show_entries', 
            'format=duration', '-of', 'default=noprint_wrappers=1:nokey=1', audio_path
        ]
        result = subprocess.run(cmd, stdout=subprocess.PIPE, text=True)
        return float(result.stdout.strip())

    def format_srt_time(self, seconds):
        ms = int((seconds - int(seconds)) * 1000)
        s = int(seconds)
        m, s = divmod(s, 60)
        h, m = divmod(m, 60)
        return f"{h:02d}:{m:02d}:{s:02d},{ms:03d}"

    def generate_srt(self, text, duration, output_path):
        words = text.split()
        chunks = []
        chunk_size = 1  # 1 word per subtitle for hyper-fast popping!
        for i in range(0, len(words), chunk_size):
            chunks.append(" ".join(words[i:i+chunk_size]))
            
        time_per_chunk = duration / len(chunks)
        
        with open(output_path, 'w', encoding='utf-8') as f:
            colors = ["<font color='#FFFF00'>", "<font color='#00FF00'>", "<font color='#FFFFFF'>", "<font color='#FF00FF'>"]
            for i, chunk in enumerate(chunks):
                start_time = i * time_per_chunk
                end_time = (i + 1) * time_per_chunk
                c = colors[i % len(colors)]
                f.write(f"{i+1}\n")
                f.write(f"{self.format_srt_time(start_time)} --> {self.format_srt_time(end_time)}\n")
                f.write(f"{c}{chunk}</font>\n\n")

    def render_video(self, audio_path, srt_path, output_path, duration):
        print(f"[*] Rendering Final Video (Duration: {duration:.2f}s)...")
        
        gameplay_dur_cmd = ['ffprobe', '-v', 'error', '-show_entries', 'format=duration', '-of', 'default=noprint_wrappers=1:nokey=1', self.gameplay_vid]
        res = subprocess.run(gameplay_dur_cmd, stdout=subprocess.PIPE, text=True)
        try:
            gp_dur = float(res.stdout.strip())
            start_sec = random.uniform(0, max(0, gp_dur - duration - 10))
        except:
            start_sec = 0

        alien_flash_start = random.uniform(2, duration - 2)
        alien_flash_end = alien_flash_start + 0.3
        
        style = "Alignment=10,Fontname=Impact,Fontsize=48,PrimaryColour=&H0000FFFF,OutlineColour=&H00000000,BorderStyle=1,Outline=4,Shadow=3,MarginV=180"
        
        cmd = [
            'ffmpeg', '-y',
            '-ss', str(start_sec),
            '-i', self.gameplay_vid,
            '-i', audio_path,
            '-stream_loop', '-1', '-i', self.bgm_audio,
            '-t', str(duration),
            '-filter_complex', (
                # Visual pulse and progress bar
                f"[0:v]crop=ih*(9/16):ih,scale=1080:1920,eq=brightness='0.05*sin(t*10)',"
                "drawbox=y=0:color=red@0.9:width=iw:height=180:t=fill,"
                "drawtext=text='🚨 CRAZY STORY 🚨':fontcolor=white:fontsize=80:x=(w-text_w)/2:y=40:font='Impact',"
                f"drawtext=text='👽':fontcolor=white:fontsize=120:x=w-250:y=h/3:enable='between(t,{alien_flash_start},{alien_flash_end})',"
                # The Psychological Progress Bar at the bottom
                f"drawbox=y=h-30:color=red:width=iw*(t/{duration}):height=30:t=fill,"
                f"subtitles={srt_path}:force_style='{style}'[v];"
                "[1:a]volume=1.8[voice];"
                "[2:a]volume=0.25[bgm];"
                "[voice][bgm]amix=inputs=2:duration=first:dropout_transition=0[a]"
            ),
            '-map', '[v]',
            '-map', '[a]',
            '-c:v', 'libx264',
            '-preset', 'fast',
            '-c:a', 'aac',
            output_path
        ]
        
        subprocess.run(cmd, check=True)
        print(f"[*] Successfully rendered: {output_path}")

    def run(self):
        story = self.fetch_reddit_story()
        if not story:
            print("[!] Could not fetch story.")
            return

        ts = int(datetime.now().timestamp())
        audio_path = os.path.join(self.output_dir, f"audio_{ts}.mp3")
        srt_path = os.path.join(self.output_dir, f"subs_{ts}.srt")
        video_path = os.path.join(self.output_dir, f"final_{ts}.mp4")

        self.generate_audio(story, audio_path)
        duration = self.get_audio_duration(audio_path)
        self.generate_srt(story, duration, srt_path)
        
        self.render_video(audio_path, srt_path, video_path, duration)
        
        print("[*] Uploading to YouTube...")
        uploader = YouTubeUploader()
        uploader.upload_video(video_path)

if __name__ == "__main__":
    factory = RedditShortsFactory()
    factory.run()
