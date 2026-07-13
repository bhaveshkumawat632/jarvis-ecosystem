import os
import subprocess
import requests
import json
import asyncio
import edge_tts
import time
import random

PEXELS_API_KEY = "PEXELS_API_KEY_HERE"
OUTPUT_DIR = "/home/junglee01/jarvis_universal/outputs/30MinMovie"
os.makedirs(OUTPUT_DIR, exist_ok=True)

# Generate a long script
print("Step 1: Generating 30-min script...")
script_text = ""
paragraphs = [
    "The AI revolution is not coming; it is already here. In the span of a few years, artificial intelligence has evolved from simple algorithms to complex systems capable of creative thought, reasoning, and autonomous action. We stand at the precipice of a new era, one that will redefine what it means to be human.",
    "Millions of jobs are being transformed. The traditional 9 to 5 desk job is being automated by AI agents. But this is not a story of human obsolescence; it is a story of human adaptation. Those who learn to harness these new tools will become the architects of the future.",
    "Prompt engineering is no longer a niche skill; it is the new programming language of the 21st century. By mastering how to communicate with machines, you can multiply your productivity by orders of magnitude. A single person with the right AI tools can now achieve what once required an entire team.",
    "But with great power comes great responsibility. As AI systems become more integrated into our infrastructure, the need for cybersecurity experts has never been greater. Digital fortresses must be built to protect our data, our privacy, and our very identities.",
    "To survive and thrive in this new landscape, you must become a lifelong learner. The tools you use today may be obsolete tomorrow. Adaptability is your greatest asset. Build your portfolio, experiment with new workflows, and never stop questioning the capabilities of the technology you use.",
    "The future belongs to the hybrid professional: the artist who codes, the programmer who writes, the engineer who designs. AI is the great equalizer, breaking down the barriers between disciplines and allowing anyone with an idea to bring it to life.",
    "Do not fear the machine. Understand it. Master it. The AI revolution is not an ending, but a beginning. The question is not whether AI will change the world, but how you will shape that change. The choice is yours."
]

# Duplicate the paragraphs to make it roughly 30 minutes long
# 7 paragraphs is about 2 minutes. We need it 15 times for 30 minutes.
full_script = "\n\n".join(paragraphs * 15)

print("Step 2: Synthesizing 30-minute Voiceover (edge-tts)...")
voice_path = os.path.join(OUTPUT_DIR, "voiceover.mp3")
async def generate_voice():
    communicate = edge_tts.Communicate(full_script, "en-US-ChristopherNeural")
    await communicate.save(voice_path)

if not os.path.exists(voice_path):
    asyncio.run(generate_voice())

print("Step 3: Fetching stock videos from Pexels...")
queries = ["technology", "artificial intelligence", "robot", "cyberpunk", "computer", "matrix", "coding", "data center", "server room", "hacker", "future", "sci-fi"]

videos_to_download = 60 # We will loop these to fill 30 minutes
downloaded_videos = []

headers = {"Authorization": PEXELS_API_KEY}
for query in queries:
    url = f"https://api.pexels.com/videos/search?query={query}&per_page=10&orientation=landscape"
    try:
        r = requests.get(url, headers=headers)
        if r.status_code == 200:
            vids = r.json().get("videos", [])
            for v in vids:
                files = v.get("video_files", [])
                # Get HD files
                hd_files = [f for f in files if f.get("quality") == "hd" and f.get("width", 0) >= 1280]
                if hd_files:
                    downloaded_videos.append(hd_files[0]["link"])
    except Exception as e:
        print(f"Pexels fetch error: {e}")

downloaded_videos = list(set(downloaded_videos))[:videos_to_download]
print(f"Found {len(downloaded_videos)} unique video URLs.")

list_file_path = os.path.join(OUTPUT_DIR, "videos.txt")
with open(list_file_path, "w") as f:
    for i, link in enumerate(downloaded_videos):
        vid_path = os.path.join(OUTPUT_DIR, f"clip_{i}.mp4")
        if not os.path.exists(vid_path):
            print(f"Downloading clip {i}/{len(downloaded_videos)}...")
            try:
                r = requests.get(link, stream=True, timeout=10)
                with open(vid_path, "wb") as vf:
                    for chunk in r.iter_content(chunk_size=8192):
                        vf.write(chunk)
            except:
                pass
        
        # Scale to 1280x720 to ensure consistent concatenation
        scaled_path = os.path.join(OUTPUT_DIR, f"scaled_{i}.mp4")
        if not os.path.exists(scaled_path) and os.path.exists(vid_path):
            print(f"Scaling clip {i}...")
            subprocess.run([
                "ffmpeg", "-y", "-i", vid_path, 
                "-vf", "scale=1280:720,setdar=16/9", 
                "-c:v", "libx264", "-preset", "ultrafast", "-crf", "28", 
                "-an", scaled_path
            ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        
        if os.path.exists(scaled_path):
            f.write(f"file 'scaled_{i}.mp4'\n")

# To make it 30 mins, we need the videos to loop. The text file should just repeat the videos.
print("Expanding list to cover 30 minutes...")
with open(list_file_path, "r") as f:
    lines = f.read().splitlines()

# 60 clips * ~15s = 15 minutes. Duplicate list 4 times = 60 mins.
full_lines = lines * 4
with open(list_file_path, "w") as f:
    for line in full_lines:
        f.write(f"{line}\n")

print("Step 4: Concatenating videos with ffmpeg...")
concat_path = os.path.join(OUTPUT_DIR, "concat_video.mp4")
subprocess.run([
    "ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", list_file_path,
    "-c", "copy", concat_path
])

print("Step 5: Mixing Voiceover and cutting to voiceover length...")
final_path = "/home/junglee01/jarvis_universal/outputs/The_AI_Revolution_30_Min_Movie.mp4"
subprocess.run([
    "ffmpeg", "-y", "-i", concat_path, "-i", voice_path,
    "-c:v", "copy", "-c:a", "aac", "-map", "0:v:0", "-map", "1:a:0",
    "-shortest", final_path
])

print(f"GOAL ACCOMPLISHED! Full 30-Min Movie saved to {final_path}")
