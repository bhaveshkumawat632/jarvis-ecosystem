import os
import subprocess

os.makedirs("jarvis_os", exist_ok=True)

audios = [
    "ironman_data/audio_0.mp3",
    "ironman_data/audio_1.mp3",
    "ironman_data/audio_2.mp3",
    "ironman_data/audio_3.mp3",
    "ironman_data/audio_4.mp3"
]

texts = [
    "LOG TONY STARK - LOCATION MUMBAI LOCAL",
    "LOG PEPPER POTTS - STATUS ANGRY",
    "LOG JAMES RHODES - STATUS SEARCHING",
    "LOG HAPPY HOGAN - STATUS PANIC",
    "LOG JARVIS - TRACKING SUIT SIGNATURE"
]

videos = []

for i in range(5):
    aud = audios[i]
    out = f"jarvis_os/scene_{i}.mp4"
    txt = texts[i]
    
    # Get duration
    try:
        dur_cmd = ["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "default=noprint_wrappers=1:nokey=1", aud]
        duration = float(subprocess.check_output(dur_cmd).decode().strip()) + 1.0
    except:
        duration = 5.0

    # Complex filter for Jarvis OS
    # 1. Background grid (color=blue)
    # 2. showspectrumpic or showwaves for audio
    # 3. drawtext for typing effect
    
    # We will use showfreqs or avector
    filter_complex = (
        f"[0:a]showfreqs=s=1280x720:mode=line:fscale=log:colors=00ffff[v1];"
        f"[0:a]showwaves=s=1280x720:mode=cline:colors=0088ff:rate=25[v2];"
        f"[v1][v2]blend=all_mode=addition[v_blend];"
        f"color=c=black:s=1280x720:d={duration}[bg];"
        f"[bg][v_blend]overlay=format=auto[v_over];"
        f"[v_over]drawtext=text='{txt}':fontcolor=cyan:fontsize=48:x=50:y=50,"
        f"drawtext=text='SYSTEM PROCESSING':fontcolor=green:fontsize=24:x=50:y=120[vout]"
    )

    cmd = [
        "ffmpeg", "-y", "-i", aud,
        "-filter_complex", filter_complex,
        "-map", "[vout]", "-map", "0:a",
        "-c:v", "libx264", "-preset", "ultrafast", "-c:a", "aac",
        "-t", str(duration), out
    ]
    
    print(f"Rendering scene {i}...")
    subprocess.run(cmd, check=True)
    videos.append(out)

# Concat
with open("jarvis_os/concat.txt", "w") as f:
    for v in videos:
        f.write(f"file '{os.path.abspath(v)}'\n")

print("Concatenating into short loop...")
short_out = "/home/junglee01/jarvis_universal/outputs/Jarvis_Logs_Short.mp4"
subprocess.run(["ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", "jarvis_os/concat.txt", "-c:v", "libx264", "-c:a", "aac", short_out], check=True)

print("Looping to 1 hour...")
final_out = "/home/junglee01/jarvis_universal/outputs/Ultimate_Jarvis_OS_Movie.mp4"
subprocess.run(["ffmpeg", "-y", "-stream_loop", "-1", "-i", short_out, "-t", "3600", "-c", "copy", final_out], check=True)

print("ALL DONE")
