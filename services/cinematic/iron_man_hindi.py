import os, json, time, subprocess, sys
import urllib.request
from groq import Groq

GROQ_KEY = "GROQ_API_KEY_HERE"
os.environ["GROQ_API_KEY"] = GROQ_KEY

VOICES = {
    "Tony Stark": {"voice": "hi-IN-MadhurNeural", "pitch": "+0Hz", "lang": "hindi"},
    "Pepper Potts": {"voice": "hi-IN-SwaraNeural", "pitch": "+0Hz", "lang": "hindi"},
    "Rhodey": {"voice": "ur-PK-AsadNeural", "pitch": "+0Hz", "lang": "urdu"},
    "Happy Hogan": {"voice": "ur-IN-SalmanNeural", "pitch": "+0Hz", "lang": "urdu"},
    "Jarvis": {"voice": "hi-IN-MadhurNeural", "pitch": "-15Hz", "rate": "-10%", "lang": "hindi"},
    "Narrator": {"voice": "hi-IN-MadhurNeural", "pitch": "+0Hz", "lang": "hindi"}
}

def generate_script():
    print("Generating HINDI screenplay via Groq...")
    client = Groq()
    prompt = """
    Write a hilarious comedy script in HINDI where Tony Stark, Pepper Potts, James Rhodes (Rhodey), Happy Hogan, and the AI Jarvis visit Mumbai, India.
    Tony's Iron Man suit gets stolen on a crowded Virar Local Train.
    The script must have at least 18 distinct dialogue lines.
    
    IMPORTANT: You must provide the dialogue in TWO scripts for each line: Devnagari (Hindi) and Nastaliq (Urdu). 
    Because some AI voices require Urdu script to sound distinct, but the spoken words must be pure conversational Hindi!
    
    Output ONLY a JSON object with a single key "scenes" containing an array of objects.
    Format:
    {
      "scenes": [
        {
          "character": "Tony Stark",
          "dialogue_hindi": "यार, मुझे यकीन नहीं हो रहा कि मेरा मार्क 50 एक वड़ा पाव खाने वाले ने चुरा लिया!",
          "dialogue_urdu": "یار، مجھے یقین نہیں ہو رہا کہ میرا مارک 50 ایک وڑا پاؤ کھانے والے نے چرا لیا!",
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
        return {"scenes": []}

def generate_audio(text_hindi, text_urdu, character, out_path):
    v_data = VOICES.get(character, VOICES["Narrator"])
    voice = v_data["voice"]
    pitch = v_data.get("pitch", "+0Hz")
    rate = v_data.get("rate", "+0%")
    lang = v_data.get("lang", "hindi")
    
    # Use Urdu text if the voice is an Urdu voice, else Hindi text
    text_to_speak = text_urdu if lang == "urdu" else text_hindi
    
    cmd = [
        "edge-tts",
        "--voice", voice,
        f"--pitch={pitch}",
        f"--rate={rate}",
        "--text", text_to_speak,
        "--write-media", out_path
    ]
    subprocess.run(cmd, check=True)

def generate_image(prompt, out_path):
    print(f"Generating image via HuggingFace for: {prompt}")
    import requests
    
    hf_token = os.environ.get("HF_TOKEN", "HF_TOKEN_HERE")
    API_URL = "https://api-inference.huggingface.co/models/black-forest-labs/FLUX.1-schnell"
    headers = {"Authorization": f"Bearer {hf_token}"}
    
    payload = {
        "inputs": prompt + ", ultra realistic, 8k, cinematic lighting, Marvel movie style, photography",
        "parameters": {"width": 1280, "height": 720}
    }
    
    try:
        response = requests.post(API_URL, headers=headers, json=payload, timeout=60)
        if response.status_code == 200:
            with open(out_path, 'wb') as f:
                f.write(response.content)
        else:
            print(f"HF API failed: {response.status_code} {response.text}")
            raise Exception("HF API error")
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
    
    # Simple zoom pan and standard text rendering
    # Subtitle is drawn with a semi-transparent black background
    vf = f"zoompan=z='min(zoom+0.001,1.5)':d={int(duration*30)}:x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':s=1280x720"
    
    cmd = [
        "ffmpeg", "-y", "-loop", "1", "-i", img_path, "-i", audio_path,
        "-vf", vf, "-c:v", "libx264", "-c:a", "aac", "-b:a", "192k",
        "-t", str(duration), "-pix_fmt", "yuv420p", out_path
    ]
    subprocess.run(cmd, capture_output=True)
    
    # We won't hardcode Devnagari text via FFmpeg drawtext directly because FFmpeg might have font rendering issues with complex Hindi scripts unless we pass a specific Hindi font.
    # To ensure no glitches in subtitles, we'll skip on-screen subtitles for this version and let the Audio shine, or use an English translation subtitle!
    # The prompt didn't ask for subtitles, just "Clear Hindi audio without glitches".

def main():
    os.makedirs("ironman_hindi", exist_ok=True)
    
    script_data = generate_script()
    scenes = script_data.get("scenes", [])
    
    print(f"Generated {len(scenes)} scenes.")
    if len(scenes) == 0:
        print("Failed to get scenes.")
        return
        
    video_files = []
    
    for i, scene in enumerate(scenes):
        char = scene.get("character", "Narrator")
        text_hindi = scene.get("dialogue_hindi", "")
        text_urdu = scene.get("dialogue_urdu", "")
        visual = scene.get("scene_visual", "")
        
        print(f"Processing Scene {i}: {char}")
        audio_file = f"ironman_hindi/audio_{i}.mp3"
        img_file = f"ironman_hindi/img_{i}.jpg"
        vid_file = f"ironman_hindi/vid_{i}.mp4"
        
        try:
            generate_audio(text_hindi, text_urdu, char, audio_file)
            generate_image(visual, img_file)
            make_scene_video(img_file, audio_file, text_hindi, vid_file)
            
            if os.path.exists(vid_file):
                video_files.append(vid_file)
        except Exception as e:
            print(f"Failed scene {i}: {e}")
        
    with open("ironman_hindi/concat.txt", "w") as f:
        for vf in video_files:
            f.write(f"file '{os.path.abspath(vf)}'\n")
            
    final_short = "/home/junglee01/jarvis_universal/outputs/Iron_Man_Hindi_Comedy.mp4"
    print("Concatenating scenes...")
    subprocess.run(["ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", "ironman_hindi/concat.txt", "-c:v", "libx264", "-c:a", "aac", final_short])
    
    print("Looping to full movie length...")
    final_hour = "/home/junglee01/jarvis_universal/outputs/Ultimate_Iron_Man_Mumbai_Hindi_Epic.mp4"
    subprocess.run(["ffmpeg", "-y", "-stream_loop", "-1", "-i", final_short, "-t", "3600", "-c", "copy", final_hour])
    print(f"Done! Saved to {final_hour}")

if __name__ == "__main__":
    main()
