import os, subprocess

artifacts_dir = "/home/junglee01/.gemini/antigravity-cli/brain/8743d446-fa75-42ae-851f-174312e37855"

# The 5 successful images
images = [
    os.path.join(artifacts_dir, "scene_0_generic_1781679081133.jpg"),
    os.path.join(artifacts_dir, "scene_1_pepper_1781679103620.jpg"),
    os.path.join(artifacts_dir, "scene_2_rhodey_1781679118495.jpg"),
    os.path.join(artifacts_dir, "scene_3_happy_1781679135139.jpg"),
    os.path.join(artifacts_dir, "scene_4_jarvis_1781678929023.jpg")
]

# The 5 generated Hindi audio files
audios = [
    "ironman_data/audio_0.mp3",
    "ironman_data/audio_1.mp3",
    "ironman_data/audio_2.mp3",
    "ironman_data/audio_3.mp3",
    "ironman_data/audio_4.mp3"
]

os.makedirs("final_build", exist_ok=True)
video_files = []

for i in range(5):
    img = images[i]
    aud = audios[i]
    vid = f"final_build/scene_{i}.mp4"
    
    # Get audio duration
    dur_cmd = ["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "default=noprint_wrappers=1:nokey=1", aud]
    try:
        dur_out = subprocess.check_output(dur_cmd).decode().strip()
        duration = float(dur_out) + 0.5 
    except:
        duration = 3.0
    
    # Simple zoom pan effect
    vf = f"zoompan=z='min(zoom+0.001,1.5)':d={int(duration*30)}:x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':s=1280x720"
    
    cmd = [
        "ffmpeg", "-y", "-loop", "1", "-i", img, "-i", aud,
        "-vf", vf, "-c:v", "libx264", "-c:a", "aac", "-b:a", "192k",
        "-t", str(duration), "-pix_fmt", "yuv420p", vid
    ]
    subprocess.run(cmd, check=True)
    video_files.append(vid)

# Concatenate
with open("final_build/concat.txt", "w") as f:
    for vf in video_files:
        f.write(f"file '{os.path.abspath(vf)}'\n")

final_short = "/home/junglee01/jarvis_universal/outputs/Perfect_Hindi_Short.mp4"
subprocess.run(["ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", "final_build/concat.txt", "-c:v", "libx264", "-c:a", "aac", final_short], check=True)

# Loop to 1 hour
final_hour = "/home/junglee01/jarvis_universal/outputs/Ultimate_Iron_Man_Mumbai_Hindi_Epic.mp4"
subprocess.run(["ffmpeg", "-y", "-stream_loop", "-1", "-i", final_short, "-t", "3600", "-c", "copy", final_hour], check=True)
print("COMPLETED")
