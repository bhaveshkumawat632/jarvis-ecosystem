import os
import random
import subprocess
from datetime import datetime
import sys

sys.path.append("/home/junglee01/jarvis_ecosystem/services/autoclipper")
from youtube_uploader import YouTubeUploader

class TriviaShortsFactory:
    def __init__(self):
        self.base_dir = "/home/junglee01/jarvis_ecosystem/services/reddit_shorts"
        self.assets_dir = os.path.join(self.base_dir, "assets")
        self.output_dir = os.path.join(self.base_dir, "output")
        os.makedirs(self.assets_dir, exist_ok=True)
        os.makedirs(self.output_dir, exist_ok=True)
        
        self.gameplay_vid = os.path.join(self.assets_dir, "gameplay.mp4")
        self.bgm_audio = os.path.join(self.assets_dir, "bgm.mp3")

        self.trivia_database = [
            {"q": "Which country has the most islands in the world?", "a": "Sweden! With over 260,000 islands."},
            {"q": "What is the rarest blood type in the world?", "a": "AB Negative! Less than 1% of the population has it."},
            {"q": "Which animal can sleep for up to 3 years?", "a": "A Snail! They can hibernate for years to survive."},
            {"q": "What is the only planet that spins clockwise?", "a": "Venus! It spins backwards compared to Earth."},
            {"q": "Which body part never stops growing?", "a": "Your ears and nose! They grow your entire life."}
        ]

    def generate_tts(self, text, output_path):
        print(f"[*] Generating TTS for: {text}")
        safe_text = text.replace('"', '\\"').replace("'", "\\'")
        cmd = ['edge-tts', '--voice', 'en-US-ChristopherNeural', '--rate', '+10%', '--text', text, '--write-media', output_path]
        subprocess.run(cmd, check=True)

    def get_audio_duration(self, audio_path):
        cmd = ['ffprobe', '-v', 'error', '-show_entries', 'format=duration', '-of', 'default=noprint_wrappers=1:nokey=1', audio_path]
        res = subprocess.run(cmd, stdout=subprocess.PIPE, text=True)
        return float(res.stdout.strip())

    def render_video(self, q_audio, a_audio, output_path, q_text, a_text, q_dur, a_dur):
        timer_duration = 5.0
        total_duration = q_dur + timer_duration + a_dur
        print(f"[*] Rendering Trivia Video (Duration: {total_duration:.2f}s)...")
        
        res = subprocess.run(['ffprobe', '-v', 'error', '-show_entries', 'format=duration', '-of', 'default=noprint_wrappers=1:nokey=1', self.gameplay_vid], stdout=subprocess.PIPE, text=True)
        try:
            gp_dur = float(res.stdout.strip())
            start_sec = random.uniform(0, max(0, gp_dur - total_duration - 10))
        except:
            start_sec = 0
        
        q_end = q_dur + timer_duration
        a_start = q_dur + timer_duration
        
        q_safe = q_text.replace("'", "\u2019").replace(":", "\:")
        a_safe = a_text.replace("'", "\u2019").replace(":", "\:")

        filter_complex = (
            f"[0:v]crop=ih*(9/16):ih,scale=1080:1920,eq=brightness=-0.1[bg];"
            
            f"[bg]drawbox=y=150:color=black@0.8:width=iw:height=300:t=fill[v1];"
            f"[v1]drawtext=text='TRIVIA TIME':fontcolor=yellow:fontsize=70:x=(w-text_w)/2:y=180:font='Impact'[v2];"
            
            f"[v2]drawtext=text='{q_safe}':fontcolor=white:fontsize=50:x=(w-text_w)/2:y=300:font='Arial':borderw=3:bordercolor=black:enable='between(t,0,{q_end})'[v3];"
            
            # Timer (5..4..3..2..1)
            f"[v3]drawtext=text='%{{expr\\:5-trunc(t-{q_dur})}}':fontcolor=red:fontsize=250:x=(w-text_w)/2:y=(h-text_h)/2:font='Impact':borderw=10:bordercolor=black:enable='between(t,{q_dur},{a_start})'[v4];"
            
            # Answer Text
            f"[v4]drawbox=y=(h-200)/2:color=green@0.9:width=iw:height=200:t=fill:enable='between(t,{a_start},{total_duration})'[v5];"
            f"[v5]drawtext=text='{a_safe}':fontcolor=white:fontsize=60:x=(w-text_w)/2:y=(h-text_h)/2:font='Impact':borderw=5:bordercolor=black:enable='between(t,{a_start},{total_duration})'[v6];"

            # Progress bar
            f"[v6]drawbox=y=h-30:color=red:width=iw*(t/{total_duration}):height=30:t=fill[v_out];"

            f"[2:a]adelay={int(a_start*1000)}|{int(a_start*1000)}[a_delayed];"
            f"[3:a]volume=0.2[bgm];"
            "[1:a][a_delayed][bgm]amix=inputs=3:duration=first:dropout_transition=0[a_out]"
        )

        cmd = [
            'ffmpeg', '-y',
            '-ss', str(start_sec),
            '-i', self.gameplay_vid,
            '-i', q_audio,
            '-i', a_audio,
            '-stream_loop', '-1', '-i', self.bgm_audio,
            '-t', str(total_duration),
            '-filter_complex', filter_complex,
            '-map', '[v_out]',
            '-map', '[a_out]',
            '-c:v', 'libx264',
            '-preset', 'fast',
            '-c:a', 'aac',
            output_path
        ]
        
        subprocess.run(cmd, check=True)
        print(f"[*] Successfully rendered: {output_path}")

    def run(self):
        trivia = random.choice(self.trivia_database)
        q_text = trivia['q']
        a_text = trivia['a']

        ts = int(datetime.now().timestamp())
        q_audio = os.path.join(self.output_dir, f"q_{ts}.mp3")
        a_audio = os.path.join(self.output_dir, f"a_{ts}.mp3")
        video_path = os.path.join(self.output_dir, f"trivia_{ts}.mp4")

        self.generate_tts(q_text, q_audio)
        self.generate_tts(a_text, a_audio)
        
        q_dur = self.get_audio_duration(q_audio)
        a_dur = self.get_audio_duration(a_audio)
        
        self.render_video(q_audio, a_audio, video_path, q_text, a_text, q_dur, a_dur)
        
        print("[*] Uploading to YouTube...")
        uploader = YouTubeUploader()
        uploader.upload_video(video_path)

if __name__ == "__main__":
    factory = TriviaShortsFactory()
    factory.run()
