import os, json, subprocess, asyncio, edge_tts
from groq import Groq

os.environ["GROQ_API_KEY"] = "GROQ_API_KEY_HERE"

VOICES = {
    "Tony Stark": {"voice": "hi-IN-MadhurNeural", "pitch": "+0Hz", "lang": "hindi"},
    "Pepper Potts": {"voice": "hi-IN-SwaraNeural", "pitch": "+0Hz", "lang": "hindi"},
    "Rhodey": {"voice": "ur-PK-AsadNeural", "pitch": "+0Hz", "lang": "urdu"},
    "Happy Hogan": {"voice": "ur-IN-SalmanNeural", "pitch": "+0Hz", "lang": "urdu"},
    "Jarvis": {"voice": "hi-IN-MadhurNeural", "pitch": "-15Hz", "rate": "-10%", "lang": "hindi"},
    "Narrator": {"voice": "hi-IN-MadhurNeural", "pitch": "+0Hz", "lang": "hindi"}
}

def generate_script():
    client = Groq()
    prompt = """
    Write a hilarious comedy script in HINDI where Tony Stark, Pepper Potts, James Rhodes (Rhodey), Happy Hogan, and the AI Jarvis visit Mumbai, India.
    Tony's Iron Man suit gets stolen on a crowded Virar Local Train.
    The script must have exactly 10 distinct dialogue lines.
    
    IMPORTANT: Provide Devnagari (Hindi) and Nastaliq (Urdu) scripts for each.
    
    Output ONLY a JSON object:
    {
      "scenes": [
        {
          "character": "Tony Stark",
          "dialogue_hindi": "यार, मुझे यकीन नहीं हो रहा!",
          "dialogue_urdu": "یار، مجھے یقین نہیں ہو رہا!",
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
        return json.loads(res.choices[0].message.content)
    except Exception as e:
        print(f"Groq error: {e}")
        return {"scenes": []}

async def main():
    os.makedirs("ironman_data", exist_ok=True)
    script_data = generate_script()
    scenes = script_data.get("scenes", [])
    
    with open("ironman_data/scenes.json", "w") as f:
        json.dump(scenes, f)
        
    for i, scene in enumerate(scenes):
        char = scene.get("character", "Narrator")
        text_hindi = scene.get("dialogue_hindi", "")
        text_urdu = scene.get("dialogue_urdu", "")
        
        v_data = VOICES.get(char, VOICES["Narrator"])
        voice = v_data["voice"]
        pitch = v_data.get("pitch", "+0Hz")
        rate = v_data.get("rate", "+0%")
        lang = v_data.get("lang", "hindi")
        text_to_speak = text_urdu if lang == "urdu" else text_hindi
        
        audio_file = f"ironman_data/audio_{i}.mp3"
        subprocess.run([
            "edge-tts", "--voice", voice, f"--pitch={pitch}", f"--rate={rate}",
            "--text", text_to_speak, "--write-media", audio_file
        ], check=True)
        
    print("DONE_JSON")

if __name__ == "__main__":
    asyncio.run(main())
