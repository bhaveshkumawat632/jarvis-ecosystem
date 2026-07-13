import os
import requests
import random
import asyncio
import edge_tts
from moviepy import VideoFileClip, AudioFileClip, CompositeAudioClip, CompositeVideoClip, concatenate_videoclips, vfx

PEXELS_API_KEY = "PEXELS_API_KEY_HERE"
OUTPUT_DIR = "/home/junglee01/jarvis_universal/outputs"
TEMP_DIR = "/home/junglee01/jarvis_universal/temp"
os.makedirs(OUTPUT_DIR, exist_ok=True)
os.makedirs(TEMP_DIR, exist_ok=True)

prompt_text = "A highly detailed 3D animated cinematic shot of a tiny astronaut in a detailed white spacesuit, standing on the surface of a purple alien planet. The background features a purple sky, floating cosmic dust, and strange rock formations. The astronaut is looking down at a large, glowing orange gem that is resting on the frozen ground. The camera performs a slow tilt-down to reveal the gem, followed by a gentle pan-right showing the surreal landscape. Soft, cinematic volumetric lighting illuminates the scene, creating a sense of awe and discovery."

print("[1/4] Generating Voiceover...")
voice_path = os.path.join(TEMP_DIR, "astronaut_voice_pexels.mp3")
async def generate_voice():
    communicate = edge_tts.Communicate(prompt_text, "en-US-ChristopherNeural")
    await communicate.save(voice_path)
asyncio.run(generate_voice())
voice_clip = AudioFileClip(voice_path)
total_duration = voice_clip.duration + 2.0

print("[2/4] Fetching Stock Video from Pexels API...")
def get_pexels_video(query, duration_needed):
    headers = {"Authorization": PEXELS_API_KEY}
    url = f"https://api.pexels.com/videos/search?query={query}&per_page=15"
    response = requests.get(url, headers=headers).json()
    
    videos = response.get("videos", [])
    if not videos: return None
    
    for v in videos:
        files = v.get("video_files", [])
        # Find 1080p or highest res
        files.sort(key=lambda x: x.get("width", 0), reverse=True)
        for f in files:
            if f.get("link"):
                return f["link"]
    return None

astronaut_url = get_pexels_video("astronaut in space", total_duration)
planet_url = get_pexels_video("alien planet or purple galaxy", total_duration)

if not astronaut_url:
    astronaut_url = get_pexels_video("space", total_duration)

print("Downloading Pexels assets...")
v1_path = os.path.join(TEMP_DIR, "v1.mp4")
v2_path = os.path.join(TEMP_DIR, "v2.mp4")

with open(v1_path, "wb") as f: f.write(requests.get(astronaut_url).content)
if planet_url:
    with open(v2_path, "wb") as f: f.write(requests.get(planet_url).content)

print("[3/4] Compositing Video...")
c1 = VideoFileClip(v1_path)
# Ensure we fill the screen
c1 = c1.resized(height=720)
c1 = c1.cropped(x_center=c1.w/2, y_center=c1.h/2, width=1280, height=720)

clips = [c1]

if planet_url:
    c2 = VideoFileClip(v2_path)
    c2 = c2.resized(height=720)
    c2 = c2.cropped(x_center=c2.w/2, y_center=c2.h/2, width=1280, height=720)
    clips.append(c2)

if sum([c.duration for c in clips]) < total_duration:
    # Loop the last clip to fill time
    clips.append(clips[-1].with_effects([vfx.Loop(duration=total_duration)]))

final_visual = concatenate_videoclips(clips, method="compose")
final_visual = final_visual.subclipped(0, total_duration)

final_video = final_visual.with_audio(voice_clip.with_start(1.0))

output_path = os.path.join(OUTPUT_DIR, "Pexels_Cinematic_Astronaut.mp4")
print("[4/4] Exporting Final Render...")
final_video.write_videofile(
    output_path, 
    fps=30, 
    codec="libx264", 
    audio_codec="aac",
    logger=None
)
print(f"DONE! File saved to {output_path}")
