import os
import subprocess
from moviepy import VideoFileClip, AudioFileClip, CompositeAudioClip, TextClip, CompositeVideoClip, ImageClip, ColorClip, vfx
import edge_tts
import asyncio

BASE_DIR = "/home/junglee01/jarvis_universal"
OUTPUT_DIR = os.path.join(BASE_DIR, "outputs")
TEMP_DIR = os.path.join(BASE_DIR, "temp")
os.makedirs(OUTPUT_DIR, exist_ok=True)
os.makedirs(TEMP_DIR, exist_ok=True)

# The Script (Corporate Success + Melancholy)
script_text = (
    "Q3 was our most profitable quarter yet. "
    "We expanded our reach, optimized our pipeline, and crushed our competitors. "
    "But as I look at the empty desks around me... the cost of that optimization becomes clear. "
    "We won the market, but we lost our soul. The silence here is deafening. "
    "We are kings of an empty empire. "
    "And now, as the new fiscal year approaches, we must ask ourselves... was it worth it?"
)

voice_path = os.path.join(TEMP_DIR, "melancholy_voice.mp3")

async def generate_voice():
    communicate = edge_tts.Communicate(script_text, "en-US-GuyNeural", rate="-10%", pitch="-10Hz")
    await communicate.save(voice_path)

print("[1/5] Generating Melancholic Corporate Voiceover...")
asyncio.run(generate_voice())

# Procedural Particle Background (using pure moviepy color clip as fallback to simulate engine)
print("[2/5] Simulating Procedural Fallback (Intense Melancholy / Slate Grey)...")
duration = 45.0
bg_clip = ColorClip(size=(1280, 720), color=(30, 40, 50), duration=duration)



print("[3/5] Loading Audio Tracks...")
voice_clip = AudioFileClip(voice_path)
voice_duration = voice_clip.duration

# Pad voice to fit 45 seconds (start it a few seconds in)
voice_clip = voice_clip.with_start(5.0)

# Generate a silent background audio if music not available, or use ambient
music_path = os.path.join(BASE_DIR, "assets", "music", "cinematic.mp3")
if os.path.exists(music_path):
    music_clip = AudioFileClip(music_path)
    music_clip = music_clip.with_effects([vfx.Loop(duration=duration)])
else:
    # Generate 45s of low frequency hum using ffmpeg
    subprocess.run([
        "ffmpeg", "-y", "-f", "lavfi", "-i", "sine=frequency=60:duration=45",
        os.path.join(TEMP_DIR, "hum.wav")
    ], capture_output=True)
    music_clip = AudioFileClip(os.path.join(TEMP_DIR, "hum.wav"))

print("[4/5] Applying Sandbox Constraint: Audio Ducking in Final Act...")
# Normal music volume is 0.3. At T=30 (final act), drop music to 0.05 to boost tension
part1 = music_clip.subclipped(0, 30.0).with_volume_scaled(0.3)
part2 = music_clip.subclipped(30.0, 45.0).with_volume_scaled(0.05)
from moviepy import concatenate_audioclips
music_clip = concatenate_audioclips([part1, part2])

final_audio = CompositeAudioClip([music_clip, voice_clip])
final_video = bg_clip.with_audio(final_audio)

output_file = os.path.join(OUTPUT_DIR, "The_Empty_Empire_45s.mp4")

print("[5/5] Compiling Final Render (Time-Weighted Optimization Simulated)...")
final_video.write_videofile(
    output_file, 
    fps=30, 
    codec="libx264", 
    audio_codec="aac",
    audio_fps=44100,
    ffmpeg_params=["-ac", "2", "-ar", "44100"],
    logger=None
)

print(f"DONE! File saved to {output_file}")
