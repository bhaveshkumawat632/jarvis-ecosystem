import os, json, time, subprocess, sys
import urllib.request
import asyncio
import edge_tts
from groq import Groq

GROQ_KEY = "GROQ_API_KEY_HERE"
os.environ["GROQ_API_KEY"] = GROQ_KEY

VOICES = {
    "Tony Stark": "en-US-ChristopherNeural",
    "Pepper Potts": "en-US-JennyNeural",
    "Rhodey": "en-US-EricNeural",
    "Happy Hogan": "en-US-GuyNeural",
    "Jarvis": "en-GB-RyanNeural",
    "Narrator": "en-US-SteffanNeural"
}

def generate_script():
    print("Generating screenplay via Groq...")
    client = Groq()
    prompt = """
    Write a hilarious comedy script where Tony Stark, Pepper Potts, James Rhodes (Rhodey), Happy Hogan, and the AI Jarvis visit Mumbai, India.
    Tony's Iron Man suit gets stolen on a crowded Virar Local Train.
    The script must have at least 15 distinct dialogue lines.
    Output ONLY a JSON object with a single key "scenes" containing an array of objects.
    Format:
    {
      "scenes": [
        {
          "character": "Tony Stark",
          "dialogue": "I can't believe my Mark 50 was stolen by a guy eating Vada Pav!",
          "scene_visual": "Tony Stark looking shocked inside a crowded Mumbai local train, cinematic lighting, highly detailed."
        }
      ]
    }
    """
    try:
        res = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[{"role": "user", "content": prompt}],
            response_format={"type": "json_object"},
        )
        content = res.choices[0].message.content
        return json.loads(content)
    except Exception as e:
        print(f"Groq error: {e}")
        return {"scenes": [
            {"character": "Tony Stark", "dialogue": "Jarvis, where is my suit?", "scene_visual": "Tony Stark in Mumbai local train looking confused."},
            {"character": "Jarvis", "dialogue": "Sir, it appears to be heading towards Andheri.", "scene_visual": "Holographic display showing Mumbai map."}
        ]}

async def generate_audio(text, character, out_path):
    voice = VOICES.get(character, VOICES["Narrator"])
    communicate = edge_tts.Communicate(text, voice)
    await communicate.save(out_path)

def generate_image(prompt, out_path):
    print(f"Generating FLUX image for: {prompt}")
    import urllib.parse
    safe_prompt = urllib.parse.quote(prompt + ", ultra realistic, 8k, cinematic lighting, Marvel movie style, ultra detailed characters")
    url = f"https://image.pollinations.ai/prompt/{safe_prompt}?width=1280&height=720&model=flux&nologo=true"
    try:
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req) as response, open(out_path, 'wb') as out_file:
            out_file.write(response.read())
    except Exception as e:
        print(f"Image gen failed: {e}")
        subprocess.run(["ffmpeg", "-y", "-f", "lavfi", "-i", "color=c=black:s=1280x720", "-frames:v", "1", out_path], capture_output=True)

def make_scene_video(img_path, audio_path, text, out_path):
    dur_cmd = ["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "default=noprint_wrappers=1:nokey=1", audio_path]
    try:
        dur_out = subprocess.check_output(dur_cmd).decode().strip()
        duration = float(dur_out) + 0.5 
    except:
        duration = 3.0
    
    safe_text = text.replace("'", "").replace(":", "\\:").replace(",", "\\,").replace('"', '\\"')
    
    # Clean zoompan effect that scales perfectly
    vf = f"zoompan=z='min(zoom+0.001,1.5)':d={int(duration*30)}:x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':s=1280x720,drawtext=text='{safe_text}':fontcolor=white:fontsize=40:box=1:boxcolor=black@0.6:boxborderw=10:x=(w-text_w)/2:y=h-th-40"
    
    cmd = [
        "ffmpeg", "-y", "-loop", "1", "-i", img_path, "-i", audio_path,
        "-vf", vf, "-c:v", "libx264", "-c:a", "aac", "-b:a", "192k",
        "-t", str(duration), "-pix_fmt", "yuv420p", out_path
    ]
    subprocess.run(cmd, capture_output=True)

async def main():
    os.makedirs("ironman_temp", exist_ok=True)
    
    script_data = generate_script()
    scenes = script_data.get("scenes", [])
    
    print(f"Generated {len(scenes)} scenes.")
    if len(scenes) == 0:
        print("Failed to get scenes.")
        return
        
    video_files = []
    
    for i, scene in enumerate(scenes):
        char = scene.get("character", "Narrator")
        text = scene.get("dialogue", "")
        visual = scene.get("scene_visual", "")
        
        print(f"Processing Scene {i}: {char}")
        audio_file = f"ironman_temp/audio_{i}.mp3"
        img_file = f"ironman_temp/img_{i}.jpg"
        vid_file = f"ironman_temp/vid_{i}.mp4"
        
        await generate_audio(text, char, audio_file)
        generate_image(visual, img_file)
        make_scene_video(img_file, audio_file, f"{char}: {text}", vid_file)
        
        if os.path.exists(vid_file):
            video_files.append(vid_file)
        else:
            print(f"Failed to create video for scene {i}")
        
    with open("ironman_temp/concat.txt", "w") as f:
        for vf in video_files:
            f.write(f"file '{os.path.abspath(vf)}'\n")
            
    final_short = "/home/junglee01/jarvis_universal/outputs/Iron_Man_Mumbai_Comedy_Short.mp4"
    print("Concatenating scenes...")
    subprocess.run(["ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", "ironman_temp/concat.txt", "-c:v", "libx264", "-c:a", "aac", final_short])
    
    print("Looping to 1 hour...")
    final_hour = "/home/junglee01/jarvis_universal/outputs/Ultimate_Iron_Man_Mumbai_Epic_1_Hour.mp4"
    subprocess.run(["ffmpeg", "-y", "-stream_loop", "-1", "-i", final_short, "-t", "3600", "-c", "copy", final_hour])
    print(f"Done! Saved to {final_hour}")

if __name__ == "__main__":
    asyncio.run(main())
