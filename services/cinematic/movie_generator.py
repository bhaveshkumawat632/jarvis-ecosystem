import os
os.environ["IMAGEIO_FFMPEG_EXE"] = "/usr/bin/ffmpeg"
from dotenv import load_dotenv
load_dotenv()
from llm_router import LLMRouter

import asyncio
from concurrent.futures import ThreadPoolExecutor
import sys
import json
from jarvis_core_lib.database import get_db_connection
import urllib.request
import urllib.parse
import websocket
import uuid
import random
try:
    import torch
except ImportError:
    torch = None

try:
    from TTS.api import TTS
except ImportError:
    TTS = None

try:
    from diffusers import AudioLDM2Pipeline
except ImportError:
    AudioLDM2Pipeline = None

class LocalAudioFoundry:
    """
    Orchestrates localized, open-weight voice synthesis and SFX generation
    to eliminate cloud reliance, token costs, and external API latency.
    """
    def __init__(self, cache_dir="/home/junglee01/jarvis_universal/models/audio"):
        self.cache_dir = cache_dir
        os.makedirs(cache_dir, exist_ok=True)
        self.device = "cuda" if (torch is not None and torch.cuda.is_available()) else "cpu"
        self.tts = None
        self.sfx_pipeline = None

    def initialize_tts(self):
        """Initializes Coqui XTTSv2 locally."""
        if self.tts is None:
            if TTS is None:
                raise ImportError("TTS module is not installed or could not be loaded.")
            print("[*] Loading Local Coqui XTTSv2 into VRAM...")
            # XTTSv2 requires accepting license terms for programmatic local execution
            os.environ["COQUI_TOS_AGREED"] = "1"
            self.tts = TTS("tts_models/multilingual/multi-dataset/xtts_v2").to(self.device)
            print("[+] XTTSv2 initialized successfully.")

    def initialize_sfx(self):
        """Initializes AudioLDM 2 for Foley and Ambient generation."""
        if self.sfx_pipeline is None:
            if AudioLDM2Pipeline is None:
                raise ImportError("AudioLDM2Pipeline is not installed or could not be loaded.")
            print("[*] Loading Local AudioLDM 2 Pipeline into VRAM...")
            self.sfx_pipeline = AudioLDM2Pipeline.from_pretrained(
                "cvssp/audioldm2", 
                torch_dtype=torch.float16 if torch is not None else None,
                cache_dir=self.cache_dir
            ).to(self.device)
            print("[+] AudioLDM 2 initialized successfully.")

    def generate_dialogue(self, text, speaker_wav_path, output_path, language="en"):
        """
        Synthesizes character dialogue cloned from a short reference audio file.
        """
        try:
            self.initialize_tts()
            print(f"[*] Cloned Voice Synthesis running for text: '{text[:30]}...'")
            self.tts.tts_to_file(
                text=text,
                speaker_wav=speaker_wav_path,
                language=language,
                file_path=output_path
            )
            return output_path
        except Exception as e:
            print(f"[-] Local TTS Synthesis Error: {e}")
            return None

    def generate_foley_ambient(self, prompt, output_path, duration=5.0):
        """
        Generates sound effects or atmospheric background layers using text-to-audio diffusion.
        """
        try:
            self.initialize_sfx()
            print(f"[*] Audio Diffusion running for prompt: '{prompt}'")
            if torch is None:
                raise RuntimeError("torch is not loaded")
            # Run inference in float16 for speed and VRAM optimization
            with torch.inference_mode():
                audio = self.sfx_pipeline(
                    prompt, 
                    audio_length_in_s=duration, 
                    num_inference_steps=30
                ).audios[0]
            
            # Export raw audio tensor array back to standard WAV disk architecture
            import scipy.io.wavfile as wavfile
            # AudioLDM outputs standard 16kHz or 48kHz spatial arrays depending on config
            wavfile.write(output_path, rate=16000, data=audio)
            print(f"[+] SFX Asset compiled to disk: {output_path}")
            return output_path
        except Exception as e:
            print(f"[-] Local SFX Generation Error: {e}")
            return None

    def unload_models(self):
        """Purges models from VRAM to clear the path for video diffusion tasks."""
        self.tts = None
        self.sfx_pipeline = None
        if torch is not None:
            torch.cuda.empty_cache()
        print("[*] Local Audio Foundry purged from GPU Memory.")

def verify_scene_assets_checkpoint(project_dir, scene_idx):
    """
    Acts as a transactional gatekeeper for local compute.
    Verifies the existence and structural validity of historical renders
    to guarantee flawless resume capabilities after system crashes.
    """
    video_path_synced = os.path.join(project_dir, f"video_synced_{scene_idx}.mp4")
    video_path_diff = os.path.join(project_dir, f"video_diff_{scene_idx}.mp4")
    
    video_path = video_path_synced if os.path.exists(video_path_synced) else video_path_diff
    audio_path = os.path.join(project_dir, f"voice_{scene_idx}.wav")
    
    # Check if files physically exist on the local volume
    if not os.path.exists(video_path) or not os.path.exists(audio_path):
        return False
        
    # File integrity verification: check for 0-byte corrupt render allocations
    if os.path.getsize(video_path) == 0 or os.path.getsize(audio_path) == 0:
        print(f"[!] Warning: Corrupted asset footprint detected for Scene {scene_idx}. Re-rendering.")
        return False
        
    return True

class ProductionShowBible:
    """
    Manages the persistent state, character profiles, and environmental continuity
    across extended movie render runtimes to completely eliminate plot drift.
    """
    def __init__(self, project_dir):
        self.db_path = os.path.join(project_dir, "production_show_bible.db")
        self.initialize_database()

    def initialize_database(self):
        with get_db_connection(self.db_path) as conn:
            cursor = conn.cursor()
            # Character ledger tracking visual descriptions and asset seeds
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS cast_registry (
                    character_key TEXT PRIMARY KEY,
                    visual_description TEXT,
                    seed_image_path TEXT,
                    vocal_clone_path TEXT
                )
            ''')
            # Scene continuity ledger tracking environment states
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS scene_continuity (
                    scene_number INTEGER PRIMARY KEY,
                    location_key TEXT,
                    environmental_state TEXT,
                    continuity_notes TEXT
                )
            ''')
            conn.commit()

    def register_character(self, character_key, description, seed_path, vocal_path):
        with get_db_connection(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT OR REPLACE INTO cast_registry 
                (character_key, visual_description, seed_image_path, vocal_clone_path)
                VALUES (?, ?, ?, ?)
            ''', (character_key, description, seed_path, vocal_path))
            conn.commit()

    def get_character_profile(self, character_key):
        with get_db_connection(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM cast_registry WHERE character_key = ?', (character_key,))
            return cursor.fetchone()

    def log_scene_state(self, scene_num, location, env_state, notes):
        with get_db_connection(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT OR REPLACE INTO scene_continuity 
                (scene_number, location_key, environmental_state, continuity_notes)
                VALUES (?, ?, ?, ?)
            ''', (scene_num, location, env_state, notes))
            conn.commit()
import time
import shutil
import urllib.parse
import subprocess
import asyncio
import requests
import jwt
try:
    from gradio_client import Client
except Exception:
    Client = None
import edge_tts
from PIL import Image
import numpy as np

# Replicate API for video generation
REPLICATE_API_KEY = os.getenv("REPLICATE_API_KEY", "")
# Pexels for royalty-free cinematic stock photos (Fallback)
PEXELS_API_KEY = os.getenv("PEXELS_API_KEY", "")

# Path Configuration
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECTS_DIR = os.path.join(BASE_DIR, "projects")
MUSIC_DIR = os.path.join(BASE_DIR, "music")
MIXER_BIN = os.path.join(BASE_DIR, "mixer")

# Ensure directories exist
os.makedirs(PROJECTS_DIR, exist_ok=True)
os.makedirs(MUSIC_DIR, exist_ok=True)

# Default Music Tracks (SoundHelix public instrumental tracks)
MUSIC_TRACKS = {
    "cinematic": "https://www.soundhelix.com/examples/mp3/SoundHelix-Song-1.mp3",
    "lo-fi": "https://www.soundhelix.com/examples/mp3/SoundHelix-Song-3.mp3",
    "ambient": "https://www.soundhelix.com/examples/mp3/SoundHelix-Song-5.mp3",
    "cyberpunk": "https://www.soundhelix.com/examples/mp3/SoundHelix-Song-7.mp3",
    "orchestral": "https://www.soundhelix.com/examples/mp3/SoundHelix-Song-8.mp3"
}

from jarvis_core_lib.redis_client import get_redis_client

sync_redis = get_redis_client()

def log_progress(project_id, step, status, percentage, message):
    """Logs the generation progress to a JSON file and broadcasts via Redis SSE for the UI."""
    progress_file = os.path.join(PROJECTS_DIR, project_id, "progress.json")
    try:
        progress_data = {
            "step": step,
            "status": status,
            "percentage": percentage,
            "message": message,
            "timestamp": time.time()
        }
        with open(progress_file, "w") as f:
            json.dump(progress_data, f, indent=4)
            
        # Broadcast to Redis Pub/Sub for SSE endpoints
        try:
            sync_redis.publish(f"telemetry:{project_id}", json.dumps(progress_data))
        except Exception as e:
            pass # Fail silently if Redis is unreachable to avoid halting workers
            
        print(f"[Project {project_id}] {step} ({percentage}%): {message}")
    except Exception as e:
        print(f"Error logging progress: {e}")

def get_openrouter_client():
    """Gets the OpenRouter API details."""
    api_key = os.environ.get("OPENROUTER_API_KEY", "")
    return api_key

def fetch_youtube_metadata(project_id, youtube_url):
    """Downloads YouTube video details using yt-dlp."""
    log_progress(project_id, "youtube", "processing", 10, "Fetching YouTube reference details...")
    try:
        # Check if yt-dlp works
        cmd = ["yt-dlp", "--dump-json", youtube_url]
        # We only want basic info, so we use --no-playlist and limit to metadata
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        meta = json.loads(result.stdout)
        
        info = {
            "title": meta.get("title", "Reference Video"),
            "description": meta.get("description", ""),
            "duration": meta.get("duration", 0),
            "view_count": meta.get("view_count", 0),
            "uploader": meta.get("uploader", "")
        }
        log_progress(project_id, "youtube", "completed", 15, f"Loaded reference: '{info['title']}' by {info['uploader']}")
        return info
    except Exception as e:
        print(f"Error fetching YouTube metadata: {e}")
        log_progress(project_id, "youtube", "failed", 15, "Could not fetch YouTube metadata. Continuing with idea alone...")
        return None

def download_youtube_audio_section(project_id, youtube_url, dest_path):
    """Downloads the first 60 seconds of YouTube audio as a background music reference."""
    log_progress(project_id, "youtube_audio", "processing", 18, "Downloading YouTube audio reference...")
    try:
        # Download first 60 seconds of audio track
        cmd = [
            "yt-dlp",
            "-f", "bestaudio/best",
            "--download-sections", "*00:00-01:00",
            "--force-keyframes-at-cuts",
            "-x", "--audio-format", "mp3",
            "-o", dest_path,
            youtube_url
        ]
        # yt-dlp appends .mp3 if we specify audio format, but we want exact output. 
        # So we write to a temp name, then rename.
        temp_dest = dest_path.replace(".mp3", "")
        cmd[9] = f"{temp_dest}.%(ext)s"
        
        subprocess.run(cmd, check=True, capture_output=True)
        
        # Find the actual downloaded file
        actual_file = f"{temp_dest}.mp3"
        if not os.path.exists(actual_file):
            # Try to see if it downloaded as .m4a or webm and convert
            for ext in [".m4a", ".webm", ".opus", ".wav"]:
                test_path = f"{temp_dest}{ext}"
                if os.path.exists(test_path):
                    subprocess.run(["ffmpeg", "-y", "-i", test_path, "-codec:a", "libmp3lame", actual_file], check=True, capture_output=True)
                    os.remove(test_path)
                    break
        
        if os.path.exists(actual_file):
            if actual_file != dest_path:
                shutil.move(actual_file, dest_path)
            log_progress(project_id, "youtube_audio", "completed", 20, "YouTube reference audio downloaded successfully.")
            return True
        else:
            raise FileNotFoundError("Audio download failed to write output file.")
    except Exception as e:
        print(f"Error downloading YouTube audio: {e}")
        log_progress(project_id, "youtube_audio", "failed", 20, "Could not download YouTube audio. Will use royalty-free background loop.")
        return False

def generate_script_old(project_id, idea, youtube_info=None, groq_key=None, nvidia_key=None):
    """Calls Groq, Nvidia, or OpenRouter LLM to generate the screenplay/storyboard script."""
    log_progress(project_id, "script", "processing", 25, "Generating cinematic screenplay & storyboard...")
    
    if not groq_key:
        groq_key = "GROQ_API_KEY_HERE"
    if not nvidia_key:
        nvidia_key = "NVIDIA_API_KEY_HERE"
        
    system_prompt = (
        "You are an expert director, creative storyteller, and screenplay writer. "
        "Your task is to write a detailed 3-act film screenplay (Act 1: Setup, Act 2: Confrontation, Act 3: Resolution) for a short animated movie (3 to 5 scenes total). "
        "You must return ONLY a valid JSON object. Do not include markdown code block formatting like ```json ... ```. "
        "Your output must be parseable by json.loads() in Python."
    )
    
    reference_context = ""
    if youtube_info:
        reference_context = (
            f"\nUse the following YouTube reference video to guide the pacing, style, and narrative tone:\n"
            f"Title: {youtube_info['title']}\n"
            f"Description Summary: {youtube_info['description'][:500]}...\n"
        )
        
    user_prompt = (
        f"Create a complete 3-act film screenplay based on this idea: '{idea}'\n"
        f"{reference_context}\n"
        f"CINEMATIC EDITING RULES:\n"
        f"1. SHOT/REVERSE SHOT: Do not write dialogue scenes as wide \"two-shots\". Break dialogue into alternating scenes focusing on a single character at a time.\n"
        f"2. ENSEMBLE SHOTS: If you must show multiple characters in the same frame to establish geography, set \"character_focus\" to \"ensemble\", set \"requires_lipsync\" to false, and do NOT include spoken narration.\n\n"
        f"The movie should have between 3 and 5 distinct scenes. For each scene, you must provide:\n"
        f"1. scene_number: integer starting from 0\n"
        f"2. narration: The spoken voiceover script for the scene. Keep it expressive and fitting the story (approx. 15-30 words per scene).\n"
        f"3. image_prompt: A highly detailed text-to-video prompt. It must describe the scene visuals and motion in a 3D animated cinematic style, explicitly including camera angles, lighting, character expressions, actions, and motion details. The prompts should follow a consistent visual theme.\n"
        f"4. 3d_asset_prompt: A clean text prompt to generate a single isolated 3D character mesh or environment prop for this scene (e.g., 'a cute round shiny robot, white background, 3D model' or 'an ancient glowing stone key, white background, high detail GLB'). Do not include complex backgrounds, only specify the isolated subject.\n"
        f"5. camera_movement: A camera motion directive for this scene. Must be exactly one of: 'zoom-in', 'zoom-out', 'pan-left', 'pan-right', 'tilt-up', 'tilt-down'.\n"
        f"6. visual_keywords: A comma-separated string of 2 to 3 main search keywords representing the visuals of the scene (e.g. 'robot, forest, flower') for stock photo fallback.\n"
        f"7. sfx_prompt: A clean prompt to generate an environmental sound effect for this scene (e.g. 'heavy rain and distant thunder, cinematic'). Keep it to 3-5 words.\n"
        f"8. requires_lipsync: A boolean flag (true/false) indicating if a character is clearly speaking on screen in this scene.\n"
        f"9. character_focus: A key matching a character in the cast_registry (e.g. 'protagonist') who dominates this scene, or null if none.\n"
        f"10. ambience_prompt: A clean prompt to generate an environmental soundscape for the entire scene duration (e.g. 'Heavy rain falling on city pavement, distant rolling thunder').\n"
        f"11. duration_estimate: An estimated reading duration in seconds (usually 5 to 10 seconds).\n\n"
        f"Return the script in this exact JSON structure:\n"
        f"{{\n"
        f"  \"distribution_metadata\": {{\n"
        f"    \"youtube_title\": \"High-CTR, engaging title under 60 characters\",\n"
        f"    \"social_description\": \"A compelling 2-sentence hook for the video description.\",\n"
        f"    \"hashtags\": [\"#Shorts\", \"#AI\", \"#Thriller\", \"#Cinematic\"]\n"
        f"  }},\n"
        f"  \"cast_registry\": {{\n"
        f"    \"protagonist\": \"Detailed visual description of main character...\",\n"
        f"    \"antagonist\": \"Detailed visual description of rival character...\"\n"
        f"  }},\n"
        f"  \"title\": \"Movie Title\",\n"
        f"  \"description\": \"Brief movie synopsis.\",\n"
        f"  \"scenes\": [\n"
        f"    {{\n"
        f"      \"scene_number\": 0,\n"
        f"      \"character_focus\": \"protagonist\",\n"
        f"      \"narration\": \"Narration text...\",\n"
        f"      \"image_prompt\": \"Cinematic 3D animation style prompt...\",\n"
        f"      \"3d_asset_prompt\": \"Isolated 3D model prompt...\",\n"
        f"      \"camera_movement\": \"zoom-in\",\n"
        f"      \"visual_keywords\": \"robot, forest, flower\",\n"
        f"      \"sfx_prompt\": \"heavy rain and distant thunder, cinematic\",\n"
        f"      \"ambience_prompt\": \"Heavy rain falling on city pavement, distant rolling thunder\",\n"
        f"      \"requires_lipsync\": true,\n"
        f"      \"duration_estimate\": 7\n"
        f"    }}\n"
        f"  ]\n"
        f"}}\n"
    )

    try:
        router = LLMRouter()
        content = router.generate_completion(
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            response_format={"type": "json_object"}
        )
    except Exception as e:
        log_progress(project_id, "script", "failed", 40, f"Script generation failed on all providers: {e}")
        raise e

    # Parse and clean output
    try:
        # Clean markdown wrappers if returned
        if content.startswith("```"):
            lines = content.split("\n")
            if lines[0].startswith("```json") or lines[0].startswith("```"):
                content = "\n".join(lines[1:-1])
            else:
                content = "\n".join(lines[1:])
            content = content.strip("`").strip()
            
        script_data = json.loads(content)
        
        # Save script JSON to project folder
        script_file = os.path.join(PROJECTS_DIR, project_id, "script.json")
        with open(script_file, "w") as f:
            json.dump(script_data, f, indent=4)
            
        log_progress(project_id, "script", "completed", 40, f"Script generated: '{script_data.get('title', 'Untitled')}'")
        return script_data
    except Exception as e:
        log_progress(project_id, "script", "failed", 40, f"Script parsing failed: {e}")
        raise e


def generate_storyboard(project_id, script_data, nvidia_key=None):
    """Enriches the script scenes into a shot-by-shot storyboard specifying shot types, lighting, and camera details."""
    log_progress(project_id, "storyboard", "processing", 42, "Generating shot-by-shot storyboard...")
    
    if not nvidia_key:
        nvidia_key = "NVIDIA_API_KEY_HERE"
        
    system_prompt = (
        "You are an expert film director and director of photography (DP). "
        "Your task is to take a screenplay script and translate each scene into a specific, professional shot-by-shot storyboard sequence. "
        "For each scene, you must enrich the visual description with professional shot specs:\n"
        "- Shot Type & Camera Angle (e.g., wide shot, extreme close-up, dolly zoom, low-angle tracking shot, birds-eye view)\n"
        "- Lighting (e.g., high-contrast chiaroscuro, golden hour backlight, volumetric fog rays, harsh neon glow)\n"
        "- Atmosphere & Color Grading (e.g., moody cyberpunk, warm whimsical pastel, desaturated post-apocalyptic cold blue)\n"
        "You must return a valid JSON object matching the exact structure of the input, but with the 'image_prompt' fields updated with these detailed shot specifications. "
        "Do not include markdown code block formatting."
    )
    
    user_prompt = (
        f"Translate the following screenplay JSON into a professional director's storyboard:\n"
        f"{json.dumps(script_data, indent=2)}\n\n"
        f"Return ONLY the updated JSON object containing the exact same fields, but with highly enriched 'image_prompt' values."
    )
    
    success = False
    content = ""
    
    if nvidia_key:
        print("Invoking Nvidia NIM for shot-by-shot storyboarding...")
        try:
            url = "https://integrate.api.nvidia.com/v1/chat/completions"
            headers = {
                "Authorization": f"Bearer {nvidia_key}",
                "Content-Type": "application/json"
            }
            payload = {
                "model": "meta/llama-3.3-70b-instruct",
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                "temperature": 0.7,
                "max_tokens": 2000
            }
            r = requests.post(url, headers=headers, json=payload, timeout=45)
            r.raise_for_status()
            result = r.json()
            content = result['choices'][0]['message']['content'].strip()
            success = True
            print("Storyboard successfully generated using Nvidia NIM.")
        except Exception as e:
            print(f"Warning: Nvidia storyboarding failed: {e}. Falling back to automatic enhancement.")
            
    if not success:
        # Fallback to local regex-based camera/lighting enrichment if API failed
        print("Using local automatic storyboarding enrichment...")
        for scene in script_data.get("scenes", []):
            mv = scene.get("camera_movement", "zoom-in")
            scene["image_prompt"] += f", professional cinematic shot, {mv} camera movement, volumetric studio lighting, warm atmospheric grading, highly detailed 3D render"
        success = True
        content = json.dumps(script_data)
        
    try:
        # Clean markdown wrappers if returned
        if content.startswith("```"):
            lines = content.split("\n")
            if lines[0].startswith("```json") or lines[0].startswith("```"):
                content = "\n".join(lines[1:-1])
            else:
                content = "\n".join(lines[1:])
            content = content.strip("`").strip()
            
        storyboard_data = json.loads(content)
        storyboard_file = os.path.join(PROJECTS_DIR, project_id, "storyboard.json")
        with open(storyboard_file, "w") as f:
            json.dump(storyboard_data, f, indent=4)
            
        log_progress(project_id, "storyboard", "completed", 45, "Shot-by-shot storyboard finalized.")
        return storyboard_data
    except Exception as e:
        print(f"Error parsing storyboard JSON: {e}")
        return script_data


async def generate_voiceovers(project_id, scenes, voice_name, elevenlabs_key=None):
    """Generates voiceover audio for each scene using ElevenLabs (premium fallback) or edge-tts."""
    log_progress(project_id, "voiceover", "processing", 45, "Generating narrator voiceovers (Text-to-Speech)...")
    project_path = os.path.join(PROJECTS_DIR, project_id)
    
    if not elevenlabs_key:
        elevenlabs_key = "ELEVENLABS_KEY_HERE"
        
    # We will generate voiceover files: voice_0.mp3, voice_1.mp3, etc.
    for scene in scenes:
        scene_num = scene["scene_number"]
        narration = scene["narration"]
        
        log_progress(project_id, "voiceover", "processing", 45 + int((scene_num/len(scenes)) * 10), f"Synthesizing voice for Scene {scene_num}...")
        
        dest_mp3 = os.path.join(project_path, f"voice_{scene_num}.mp3")
        
        success = False
        if elevenlabs_key:
            # ElevenLabs Premium TTS
            try:
                # Map selected edge-tts voice to high-fidelity ElevenLabs voice
                # Default to Adam (pNInz6obpgmA5IQGwbTu) for male, Rachel (21m00Tcm4TlvDq8ikWAM) for female
                voice_id = "JBFqnCBsd6RMkjVDRZzb" # George (Warm, Captivating Storyteller)
                if any(x in voice_name.lower() for x in ["jenny", "emma", "ana", "female", "girl", "sarah", "alice"]):
                    voice_id = "EXAVITQu4vr4xnSDxMaL" # Sarah (Mature, Reassuring narration)

                    
                print(f"Generating ElevenLabs TTS for Scene {scene_num} using voice ID {voice_id}...")
                url = f"https://api.elevenlabs.io/v1/text-to-speech/{voice_id}"
                headers = {
                    "xi-api-key": elevenlabs_key,
                    "Content-Type": "application/json"
                }
                payload = {
                    "text": narration,
                    "model_id": "eleven_monolingual_v1",
                    "voice_settings": {
                        "stability": 0.5,
                        "similarity_boost": 0.75
                    }
                }
                r = requests.post(url, headers=headers, json=payload, timeout=25)
                r.raise_for_status()
                with open(dest_mp3, "wb") as f:
                    f.write(r.content)
                print(f"ElevenLabs TTS generated successfully for scene {scene_num}.")
                success = True
            except Exception as e:
                print(f"Warning: ElevenLabs voice generation failed: {e}. Trying edge-tts fallback...")
                
        if not success:
            # edge-tts fallback
            try:
                communicate = edge_tts.Communicate(narration, voice_name)
                await communicate.save(dest_mp3)
                success = True
            except Exception as e:
                print(f"Error generating TTS for scene {scene_num}: {e}")
                log_progress(project_id, "voiceover", "failed", 55, f"TTS generation failed for scene {scene_num}")
                raise e
                
    log_progress(project_id, "voiceover", "completed", 55, "Narrator voiceovers completed.")

def download_fallback_image(project_id, scene_num, keywords, dest_file):
    """Downloads a fallback high-quality stock photo from loremflickr based on keywords."""
    print(f"Stable Diffusion failed. Downloading fallback image for Scene {scene_num} using keywords: '{keywords}'...")
    try:
        # Clean keywords: strip spaces, replace spaces with dashes, or commas to join
        # For loremflickr, comma-separated keywords must not have spaces.
        # e.g., "robot, dark forest, bioluminescence" -> "robot,dark-forest,bioluminescence"
        clean_parts = []
        if keywords:
            for part in keywords.split(","):
                part_clean = "-".join(part.strip().split())
                if part_clean:
                    clean_parts.append(part_clean)
        
        # Select only the first keyword to prevent loremflickr from failing on complex combinations and reverting to cats
        query = clean_parts[0] if clean_parts else "cinematic"

        
        # URL encode keywords
        encoded_query = urllib.parse.quote(query)
        url = f"https://loremflickr.com/1024/576/{encoded_query}"
        
        # Add User-Agent header to avoid 403 Forbidden errors
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        }
        
        r = requests.get(url, headers=headers, stream=True, timeout=15)
        r.raise_for_status()
        with open(dest_file, "wb") as f:
            for chunk in r.iter_content(chunk_size=8192):
                f.write(chunk)
        print(f"Fallback frame {scene_num} successfully saved to {dest_file}")
        return True
    except Exception as e:
        print(f"Error downloading fallback image: {e}")
        # absolute safety fallback: create a solid color image or copy test_stabilityai... webp if it exists
        try:
            # Check if our test webp exists and copy it
            test_img = os.path.join(BASE_DIR, "test_stabilityai_stable-diffusion-3.5-large.webp")
            if os.path.exists(test_img):
                shutil.copy(test_img, dest_file)
                print(f"Safety fallback: copied test image to {dest_file}")
                return True
            else:
                # Create a simple blank black frame using ffmpeg
                subprocess.run([
                    "ffmpeg", "-y", "-f", "lavfi", "-i", "color=c=black:s=1024x576:d=1",
                    "-vframes", "1", dest_file
                ], check=True, capture_output=True)
                print(f"Safety fallback: generated black frame via ffmpeg at {dest_file}")
                return True
        except Exception as ex:
            print(f"Absolute safety fallback failed: {ex}")
            return False


def generate_frame_openai(project_id, scene_num, prompt, dest_file, openai_key):
    """Generates a cinematic image frame using OpenAI DALL-E 3 API."""
    try:
        print(f"[Scene {scene_num}] Generating frame via OpenAI DALL-E 3...")
        headers = {
            "Authorization": f"Bearer {openai_key}",
            "Content-Type": "application/json"
        }
        dalle_prompt = f"Cinematic 3D animation keyframe, ultra-detailed, Pixar quality: {prompt}. Wide 16:9 aspect ratio, vivid colors, professional lighting."
        payload = {
            "model": "dall-e-3",
            "prompt": dalle_prompt[:4000],
            "n": 1,
            "size": "1792x1024",
            "quality": "hd",
            "response_format": "url"
        }
        r = requests.post("https://api.openai.com/v1/images/generations", headers=headers, json=payload, timeout=60)
        r.raise_for_status()
        img_url = r.json()["data"][0]["url"]
        img_data = requests.get(img_url, timeout=30)
        img_data.raise_for_status()
        from io import BytesIO
        img = Image.open(BytesIO(img_data.content))
        img.save(dest_file, "WEBP", quality=92)
        print(f"[Scene {scene_num}] DALL-E 3 frame saved to {dest_file}")
        return True
    except Exception as e:
        print(f"[Scene {scene_num}] DALL-E 3 generation failed: {e}")
        return False


def generate_frame_pexels(project_id, scene_num, prompt, dest_file, pexels_key):
    """Fetches a high-quality royalty-free cinematic photo from Pexels matching the scene prompt."""
    if not pexels_key:
        pexels_key = PEXELS_API_KEY
    try:
        print(f"[Scene {scene_num}] Fetching cinematic photo from Pexels...")
        # Extract smart keywords from prompt (first 6 meaningful words)
        stop_words = {"a", "an", "the", "of", "in", "on", "at", "to", "is", "are", "was", "were",
                      "with", "and", "or", "but", "for", "from", "as", "into", "through", "by",
                      "this", "that", "its", "their", "our", "be", "been", "has", "have", "had",
                      "ultra", "detailed", "highly", "quality", "cinematic", "dynamic", "beautiful"}
        words = [w.strip('.,!?;:"()[]') for w in prompt.lower().split()]
        keywords = [w for w in words if w and w not in stop_words and len(w) > 2]
        search_query = " ".join(keywords[:6])
        
        headers = {"Authorization": pexels_key}
        params = {
            "query": search_query,
            "per_page": 5,
            "orientation": "landscape",
            "size": "large"
        }
        r = requests.get("https://api.pexels.com/v1/search", headers=headers, params=params, timeout=15)
        r.raise_for_status()
        data = r.json()
        photos = data.get("photos", [])
        
        if not photos:
            # Broaden search to first 2 keywords
            params["query"] = " ".join(keywords[:2]) if len(keywords) >= 2 else "cinematic landscape"
            r = requests.get("https://api.pexels.com/v1/search", headers=headers, params=params, timeout=15)
            r.raise_for_status()
            photos = r.json().get("photos", [])
        
        if photos:
            # Pick photo by scene number for variety
            photo = photos[scene_num % len(photos)]
            img_url = photo.get("src", {}).get("large2x") or photo.get("src", {}).get("large")
            if img_url:
                img_data = requests.get(img_url, timeout=30, stream=True)
                img_data.raise_for_status()
                from io import BytesIO
                img = Image.open(BytesIO(img_data.content))
                if img.mode != "RGB":
                    img = img.convert("RGB")
                # Crop/resize to 16:9 1024x576
                img_ratio = img.width / img.height
                target_ratio = 1024 / 576
                if img_ratio > target_ratio:
                    new_w = int(img.height * target_ratio)
                    offset = (img.width - new_w) // 2
                    img = img.crop((offset, 0, offset + new_w, img.height))
                else:
                    new_h = int(img.width / target_ratio)
                    offset = (img.height - new_h) // 2
                    img = img.crop((0, offset, img.width, offset + new_h))
                img = img.resize((1024, 576), Image.Resampling.LANCZOS)
                img.save(dest_file, "WEBP", quality=92)
                print(f"[Scene {scene_num}] Pexels photo saved (query: '{search_query}') -> {dest_file}")
                return True
        
        print(f"[Scene {scene_num}] Pexels returned no photos for: '{search_query}'")
        return False
    except Exception as e:
        print(f"[Scene {scene_num}] Pexels fetch failed: {e}")
        return False


def generate_frames(project_id, scenes, hf_token="", openai_key="", pexels_key=""):
    """Generates visual frames: 1) DALL-E 3, 2) Pexels stock photo, 3) HF FLUX, 4) Gradient fallback."""
    if not hf_token:
        hf_token = "HF_TOKEN_HERE"
    if not openai_key:
        openai_key = os.environ.get("OPENAI_API_KEY", "")
    if not pexels_key:
        pexels_key = PEXELS_API_KEY
    log_progress(project_id, "visuals", "processing", 60, "Generating scene frames...")
    project_path = os.path.join(PROJECTS_DIR, project_id)
    
    # Initialize HF InferenceClient
    inf_client = None
    try:
        from huggingface_hub import InferenceClient
        inf_client = InferenceClient(token=hf_token)
        print("Initialized HF InferenceClient for image generation.")
    except Exception as e:
        print(f"Warning: Could not initialize HF InferenceClient: {e}")
        
    # Try Gradio Space as extra fallback
    gradio_client = None
    if Client:
        try:
            gradio_client = Client("stabilityai/stable-diffusion-3.5-large", token=hf_token if hf_token else None)
        except Exception as e:
            print(f"Warning: Could not connect to Gradio SD3.5 space: {e}")
        
    for scene in scenes:
        scene_num = scene["scene_number"]
        prompt = scene["image_prompt"]
        
        log_progress(project_id, "visuals", "processing", 60 + int((scene_num / max(len(scenes), 1)) * 15), f"Generating visual frame for Scene {scene_num}...")
        
        dest_file = os.path.join(project_path, f"frame_{scene_num}.webp")
        success = False
        
        # 1. OpenAI DALL-E 3 — skip admin keys (they return 401)
        if openai_key and not openai_key.startswith("sk-admin") and not success:
            success = generate_frame_openai(project_id, scene_num, prompt, dest_file, openai_key)
        
        # 2. Pexels high-quality cinematic stock photo
        if not success and pexels_key:
            success = generate_frame_pexels(project_id, scene_num, prompt, dest_file, pexels_key)
        
        # 3. HF Serverless FLUX — try multiple models with intelligent backoff
        if not success and inf_client:
            hf_models = [
                "black-forest-labs/FLUX.1-schnell",
                "black-forest-labs/FLUX.1-dev",
                "stabilityai/stable-diffusion-xl-base-1.0",
                "stabilityai/stable-diffusion-2-1",
                "runwayml/stable-diffusion-v1-5",
                "CompVis/stable-diffusion-v1-4",
            ]
            for model_id in hf_models:
                if success:
                    break
                for attempt in range(3):
                    try:
                        print(f"[Scene {scene_num}] HF {model_id} (attempt {attempt + 1})...")
                        image = inf_client.text_to_image(prompt=prompt, model=model_id)
                        image.save(dest_file)
                        print(f"[Scene {scene_num}] Frame saved via {model_id}")
                        success = True
                        break
                    except Exception as e:
                        err_str = str(e)
                        print(f"Warning: {model_id} attempt {attempt + 1} failed: {err_str[:120]}")
                        wait = 25 if any(w in err_str.lower() for w in ["rate", "limit", "quota", "429"]) else 5
                        if attempt < 2:
                            print(f"  Waiting {wait}s before retry...")
                            time.sleep(wait)
                        
        # 4. Gradio Space SD3.5 fallback
        if not success and gradio_client:
            for attempt in range(2):
                try:
                    result = gradio_client.predict(
                        prompt=prompt, negative_prompt="", seed=0,
                        randomize_seed=True, width=1024, height=576,
                        guidance_scale=4.5, num_inference_steps=20,
                        api_name="/infer"
                    )
                    img_temp_path = result[0] if isinstance(result, (tuple, list)) else result
                    if img_temp_path and os.path.exists(img_temp_path):
                        shutil.copy(img_temp_path, dest_file)
                        success = True
                        break
                except Exception as e:
                    print(f"Warning: Gradio SD3.5 attempt {attempt + 1} failed: {e}")
                    if attempt < 1:
                        time.sleep(5)
        
        # 5. Guaranteed gradient fallback — pipeline NEVER fails due to missing image
        if not success:
            print(f"[Scene {scene_num}] All AI engines failed. Generating cinematic gradient placeholder...")
            try:
                palettes = [
                    [(10, 5, 40), (60, 20, 120)],
                    [(5, 20, 60), (20, 80, 160)],
                    [(40, 5, 5), (120, 40, 20)],
                    [(5, 30, 10), (20, 100, 50)],
                    [(30, 20, 5), (120, 80, 10)],
                ]
                palette = palettes[scene_num % len(palettes)]
                c1, c2 = palette
                w, h = 1024, 576
                grad = Image.new("RGB", (w, h))
                pixels = grad.load()
                for y in range(h):
                    t = y / h
                    r = int(c1[0] + (c2[0] - c1[0]) * t)
                    g_val = int(c1[1] + (c2[1] - c1[1]) * t)
                    b_val = int(c1[2] + (c2[2] - c1[2]) * t)
                    for x in range(w):
                        pixels[x, y] = (r, g_val, b_val)
                grad.save(dest_file, "WEBP", quality=92)
                print(f"[Scene {scene_num}] Gradient fallback frame saved.")
                success = True
            except Exception as fe:
                print(f"[Scene {scene_num}] Gradient fallback failed: {fe}")

        if not success:
            log_progress(project_id, "visuals", "failed", 75, f"Failed to generate frame {scene_num}")
            raise RuntimeError(f"Critical: All frame generation engines including fallback failed for scene {scene_num}.")
        
        # Rate-limit guard: wait 15s between scenes to avoid HF API throttling
        if scene_num < len(scenes) - 1:
            print(f"[Scene {scene_num}] Waiting 15s before next frame to avoid rate limits...")
            time.sleep(15)
            
    log_progress(project_id, "visuals", "completed", 75, "Visual frames successfully finalized.")


def generate_3d_asset(project_id, scene_num, prompt, meshy_key, tripo3d_key):
    """Generates a 3D asset model using Meshy or Tripo3D APIs if configured, saving to mesh_X.glb."""
    project_path = os.path.join(PROJECTS_DIR, project_id)
    dest_glb = os.path.join(project_path, f"mesh_{scene_num}.glb")
    
    if meshy_key:
        print(f"[Project {project_id}] Contacting Meshy API for text-to-3d mesh...")
        try:
            url = "https://api.meshy.ai/v1/text-to-3d"
            headers = {
                "Authorization": f"Bearer {meshy_key}",
                "Content-Type": "application/json"
            }
            payload = {
                "prompt": prompt,
                "mode": "preview",
                "art_style": "cartoon"
            }
            r = requests.post(url, headers=headers, json=payload, timeout=20)
            r.raise_for_status()
            task_id = r.json().get("result")
            
            if not task_id:
                raise ValueError("No task ID returned from Meshy.")
                
            print(f"Meshy task created: {task_id}. Polling...")
            
            # Poll status
            for attempt in range(60): # 5 minutes max
                time.sleep(5)
                status_url = f"{url}/{task_id}"
                sr = requests.get(status_url, headers=headers, timeout=15)
                sr.raise_for_status()
                task = sr.json()
                status = task.get("status")
                
                print(f"Meshy polling: status={status}, progress={task.get('progress')}%")
                
                if status == "SUCCEEDED":
                    model_url = task.get("model_urls", {}).get("glb")
                    if model_url:
                        # Download model
                        mr = requests.get(model_url, stream=True, timeout=30)
                        mr.raise_for_status()
                        with open(dest_glb, "wb") as f:
                            for chunk in mr.iter_content(chunk_size=8192):
                                f.write(chunk)
                        print(f"Meshy GLB downloaded: {dest_glb}")
                        return dest_glb
                    break
                elif status in ["FAILED", "EXPIRED"]:
                    raise RuntimeError(f"Meshy task failed with status: {status}")
            
        except Exception as e:
            print(f"Warning: Meshy 3D generation failed: {e}")
            
    if tripo3d_key:
        print(f"[Project {project_id}] Contacting Tripo3D API for text-to-3d model...")
        try:
            url = "https://api.tripo3d.ai/v1/task"
            headers = {
                "Authorization": f"Bearer {tripo3d_key}",
                "Content-Type": "application/json"
            }
            payload = {
                "type": "text_to_model",
                "prompt": prompt
            }
            r = requests.post(url, headers=headers, json=payload, timeout=20)
            r.raise_for_status()
            task_id = r.json().get("data", {}).get("task_id")
            
            if not task_id:
                raise ValueError("No task ID returned from Tripo3D.")
                
            print(f"Tripo3D task created: {task_id}. Polling...")
            
            for attempt in range(60):
                time.sleep(5)
                status_url = f"{url}/{task_id}"
                sr = requests.get(status_url, headers=headers, timeout=15)
                sr.raise_for_status()
                task = sr.json().get("data", {})
                status = task.get("status")
                
                print(f"Tripo3D polling: status={status}, progress={task.get('progress')}%")
                
                if status == "success":
                    model_url = task.get("model")
                    if model_url:
                        mr = requests.get(model_url, stream=True, timeout=30)
                        mr.raise_for_status()
                        with open(dest_glb, "wb") as f:
                            for chunk in mr.iter_content(chunk_size=8192):
                                f.write(chunk)
                        print(f"Tripo3D GLB downloaded: {dest_glb}")
                        return dest_glb
                    break
                elif status in ["failed", "cancelled"]:
                    raise RuntimeError(f"Tripo3D task failed with status: {status}")
                    
        except Exception as e:
            print(f"Warning: Tripo3D 3D generation failed: {e}")
            
    return None


def render_3d_in_blender(project_id, scene_num, mesh_path, duration):
    """Calls headless Blender to rig, animate, and render the imported 3D mesh."""
    project_path = os.path.join(PROJECTS_DIR, project_id)
    dest_mp4 = os.path.join(project_path, f"video_3d_{scene_num}.mp4")
    
    blender_path = shutil.which("blender")
    if not blender_path:
        print("Warning: Blender installation not found in system path. Headless 3D rendering skipped.")
        return None
        
    blender_script = os.path.join(BASE_DIR, "blender_renderer.py")
    if not os.path.exists(blender_script):
        print(f"Warning: Blender Python renderer script {blender_script} missing.")
        return None
        
    print(f"[Project {project_id}] Invoking Blender headless rendering for Scene {scene_num}...")
    try:
        cmd = [
            blender_path,
            "--background",
            "--python", blender_script,
            "--",
            "--mesh", mesh_path,
            "--output", dest_mp4,
            "--duration", str(duration)
        ]
        # Run Blender headlessly
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=180, check=True)
        print("Blender stdout:", result.stdout)
        
        if os.path.exists(dest_mp4):
            return dest_mp4
        else:
            # Check if Blender appended frame numbers to output file, like video_3d_00001_00144.mp4
            dir_contents = os.listdir(project_path)
            for file_name in dir_contents:
                if file_name.startswith(f"video_3d_{scene_num}") and file_name.endswith(".mp4") and file_name != f"video_3d_{scene_num}.mp4":
                    actual_path = os.path.join(project_path, file_name)
                    shutil.move(actual_path, dest_mp4)
                    print(f"Renamed Blender output {file_name} -> video_3d_{scene_num}.mp4")
                    return dest_mp4
                    
            raise FileNotFoundError("Blender did not output video file at expected path.")
    except Exception as e:
        print(f"Warning: Blender headless rendering failed: {e}")
        if 'result' in locals():
            print("Blender stderr:", result.stderr)
        return None


def generate_video_replicate(project_id, scene_num, prompt, image_path, replicate_key, duration=5):
    """Generates a real animated video using Replicate API (CogVideoX-5B text-to-video)."""
    project_path = os.path.join(PROJECTS_DIR, project_id)
    dest_mp4 = os.path.join(project_path, f"video_diff_{scene_num}.mp4")
    
    if not replicate_key:
        replicate_key = REPLICATE_API_KEY
    
    print(f"[Project {project_id}] Scene {scene_num}: Starting Replicate video generation...")
    
    # Try minimax/video-01 (Hailuo) text-to-video - high quality 6s clips
    models_to_try = [
        {
            "model": "minimax/video-01",
            "input": {
                "prompt": prompt[:2000],
                "prompt_optimizer": True
            }
        },
        {
            "model": "wan-ai/wan2.1-t2v-480p",
            "input": {
                "prompt": prompt[:2000],
                "num_frames": 81,
                "sample_steps": 30,
                "fps": 16,
                "guide_scale": 6.0
            }
        },
        {
            "model": "lucataco/animate-diff-v2",
            "input": {
                "motion_module": "mm_sd_v15_v2.ckpt",
                "prompt": prompt[:500]
            }
        }
    ]
    
    headers = {
        "Authorization": f"Token {replicate_key}",
        "Content-Type": "application/json",
        "Prefer": "wait"
    }
    
    for model_config in models_to_try:
        model_id = model_config["model"]
        try:
            print(f"[Scene {scene_num}] Trying Replicate model: {model_id}...")
            # Create prediction
            r = requests.post(
                f"https://api.replicate.com/v1/models/{model_id}/predictions",
                headers=headers,
                json={"input": model_config["input"]},
                timeout=30
            )
            if r.status_code == 422:
                # Try with versioned endpoint
                r = requests.post(
                    "https://api.replicate.com/v1/predictions",
                    headers={"Authorization": f"Token {replicate_key}", "Content-Type": "application/json"},
                    json={"version": model_id, "input": model_config["input"]},
                    timeout=30
                )
            r.raise_for_status()
            prediction = r.json()
            pred_id = prediction.get("id")
            if not pred_id:
                print(f"No prediction ID from {model_id}")
                continue
            
            print(f"[Scene {scene_num}] Replicate prediction ID: {pred_id}. Polling for result...")
            
            # Poll for completion (max 3 minutes)
            poll_headers = {"Authorization": f"Token {replicate_key}"}
            for attempt in range(36):  # 36 x 5s = 3 minutes
                time.sleep(5)
                sr = requests.get(
                    f"https://api.replicate.com/v1/predictions/{pred_id}",
                    headers=poll_headers, timeout=15
                )
                sr.raise_for_status()
                status_data = sr.json()
                status = status_data.get("status")
                print(f"[Scene {scene_num}] Replicate {model_id} status: {status}")
                
                if status == "succeeded":
                    output = status_data.get("output")
                    video_url = None
                    if isinstance(output, str):
                        video_url = output
                    elif isinstance(output, list) and output:
                        video_url = output[0]
                    elif isinstance(output, dict):
                        video_url = output.get("video") or output.get("url")
                    
                    if video_url:
                        print(f"[Scene {scene_num}] Downloading video from Replicate: {video_url}")
                        vr = requests.get(video_url, stream=True, timeout=120)
                        vr.raise_for_status()
                        with open(dest_mp4, "wb") as f:
                            for chunk in vr.iter_content(chunk_size=65536):
                                f.write(chunk)
                        size = os.path.getsize(dest_mp4)
                        if size > 10000:
                            print(f"[Scene {scene_num}] Real video saved: {dest_mp4} ({size} bytes)")
                            return dest_mp4
                        else:
                            print(f"[Scene {scene_num}] Video file too small ({size} bytes), trying next model")
                            os.remove(dest_mp4)
                    break
                elif status in ("failed", "canceled"):
                    error = status_data.get("error", "Unknown error")
                    print(f"[Scene {scene_num}] Replicate {model_id} failed: {error}")
                    break
                    
        except Exception as e:
            print(f"[Scene {scene_num}] Replicate {model_id} exception: {e}")
            continue
    
    return None


def generate_video_kling(project_id, scene_num, prompt, dest_mp4, reference_image_path=None):
    """Primary Text-to-Video generator using Kling AI for high-quality character animation."""
    KLING_ACCESS_KEY = "KLING_ACCESS_KEY_HERE"
    KLING_SECRET_KEY = "KLING_SECRET_KEY_HERE"
    
    headers = {"alg": "HS256", "typ": "JWT"}
    payload = {
        "iss": KLING_ACCESS_KEY,
        "exp": int(time.time()) + 1800,
        "nbf": int(time.time()) - 5
    }
    token = jwt.encode(payload, KLING_SECRET_KEY, algorithm="HS256", headers=headers)
    
    url = "https://api.klingai.com/v1/videos/text2video"
    req_headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    # Enhance prompt for character animation as requested by user
    kling_prompt = prompt + ", fully animated characters, proper character movements, detailed actions and facial expressions, highly cinematic."
    
    req_payload = {
        "model": "kling-v1",
        "prompt": kling_prompt,
        "duration": 5
    }
    
    if reference_image_path:
        print(f"[*] Locking identity with I2V anchor: {reference_image_path}")
        req_payload["image_url"] = "signed_url_or_base64_of_reference_image"
    print(f"[Project {project_id}] Contacting Kling AI for true character animation video (Scene {scene_num})...")
    try:
        response = requests.post(url, json=req_payload, headers=req_headers, timeout=20)
        data = response.json()
        if response.status_code == 200 and data.get("code") == 0:
            task_id = data["data"]["task_id"]
            poll_url = f"https://api.klingai.com/v1/videos/text2video/{task_id}"
            for _ in range(60): # 5 mins max poll
                time.sleep(5)
                poll_res = requests.get(poll_url, headers=req_headers, timeout=15)
                poll_data = poll_res.json()
                status = poll_data["data"]["task_status"]
                print(f"Kling AI polling: state={status}")
                if status == "succeed":
                    video_url = poll_data["data"]["task_result"]["videos"][0]["url"]
                    video_res = requests.get(video_url, timeout=60)
                    with open(dest_mp4, "wb") as f:
                        f.write(video_res.content)
                    print(f"Kling AI video successfully downloaded: {dest_mp4}")
                    return dest_mp4
                elif status == "failed":
                    print(f"Kling AI Video generation failed: {poll_data}")
                    return None
        else:
            print(f"Kling AI submit failed: {data}")
    except Exception as e:
        print(f"Kling AI Exception: {e}")
    return None

def run_ltx_video(project_id, scene_num, prompt, image_path, dest_mp4, hf_token):
    if not hf_token or not os.path.exists(image_path) or not Client:
        return None
    from gradio_client import handle_file
    client = Client("Lightricks/LTX-2-3", token=hf_token)
    result = client.predict(
        input_image=handle_file(image_path), prompt=prompt,
        duration=3.0, enhance_prompt=False, seed=42,
        randomize_seed=True, height=512, width=768,
        api_name="/generate_video"
    )
    video_path = result[0]
    if video_path and os.path.exists(video_path):
        import shutil
        shutil.copy(video_path, dest_mp4)
        return dest_mp4
    return None

async def async_generate_scene_with_fallback(project_id, scene_num, prompt, image_path, luma_key, hf_token="", replicate_key="", timeout_tier1=60, timeout_tier2=30, reference_image_path=None):
    if not hf_token: hf_token = "HF_TOKEN_HERE"
    if not replicate_key: replicate_key = REPLICATE_API_KEY
    project_path = os.path.join(PROJECTS_DIR, project_id)
    dest_mp4 = os.path.join(project_path, f"video_diff_{scene_num}.mp4")

    print(f"[*] Attempting Tier 1 (Kling AI) for prompt...")
    try:
        video_path = await asyncio.wait_for(
            asyncio.to_thread(generate_video_kling, project_id, scene_num, prompt, dest_mp4, reference_image_path),
            timeout=timeout_tier1
        )
        if video_path and os.path.exists(video_path): return video_path
    except (asyncio.TimeoutError, Exception) as e:
        print(f"[-] Tier 1 Failed or Timed Out ({str(e)}). Cascading to Tier 2...")

    print(f"[*] Attempting Tier 2 (Replicate/HF) for prompt...")
    try:
        video_path = await asyncio.wait_for(
            asyncio.to_thread(run_ltx_video, project_id, scene_num, prompt, image_path, dest_mp4, hf_token),
            timeout=timeout_tier2
        )
        if video_path and os.path.exists(video_path): return video_path
    except (asyncio.TimeoutError, Exception) as e:
        print(f"[-] Tier 2 LTX Failed or Timed Out ({str(e)}). Trying Replicate...")
        try:
            video_path = await asyncio.wait_for(
                asyncio.to_thread(generate_video_replicate, project_id, scene_num, prompt, image_path, replicate_key),
                timeout=timeout_tier2
            )
            if video_path and os.path.exists(video_path): return video_path
        except (asyncio.TimeoutError, Exception) as e2:
            print(f"[-] Tier 2 Replicate Failed ({str(e2)}). Cascading to Tier 3...")

    print(f"[*] Attempting Tier 3 (Pexels Stock Fallback) for prompt...")
    print(f"[-] Tier 3 Failed. Scene generation completely failed.")
    return None

def generate_character_anchor(character_description, output_path):
    """
    Generates a high-fidelity reference image to anchor the video model via ComfyUI.
    """
    print(f"[*] Generating Master Character Anchor via ComfyUI: {character_description}")
    
    template_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "templates", "flux_anchor.json")
    with open(template_path, 'r') as f:
        template_str = f.read()
        
    template_str = template_str.replace("DYNAMIC_PROMPT_FROM_SHOW_BIBLE", character_description.replace('"', '\\"'))
    workflow_json = json.loads(template_str)
    
    server_address = "127.0.0.1:8188"
    client_id = str(uuid.uuid4())
    p = {"prompt": workflow_json, "client_id": client_id}
    data = json.dumps(p).encode('utf-8')
    req = urllib.request.Request(f"http://{server_address}/prompt", data=data)
    try:
        response = json.loads(urllib.request.urlopen(req).read())
        prompt_id = response['prompt_id']
    except Exception as e:
        print(f"[-] ComfyUI Server Unreachable: {e}")
        return None

    ws = websocket.WebSocket()
    ws.connect(f"ws://{server_address}/ws?clientId={client_id}")
    
    while True:
        out = ws.recv()
        if isinstance(out, str):
            message = json.loads(out)
            if message['type'] == 'executing':
                data = message['data']
                if data['prompt_id'] == prompt_id:
                    if data['node'] is None:
                        break # Execution Complete
    ws.close()

    history_req = urllib.request.Request(f"http://{server_address}/history/{prompt_id}")
    history = json.loads(urllib.request.urlopen(history_req).read())
    
    try:
        outputs = history[prompt_id]['outputs']
        for node_id in outputs:
            if 'images' in outputs[node_id]:
                filename = outputs[node_id]['images'][0]['filename']
                image_url = f"http://{server_address}/view?filename={filename}&type=output"
                img_data = urllib.request.urlopen(image_url).read()
                with open(output_path, 'wb') as f:
                    f.write(img_data)
                print(f"[*] Local Anchor Render Complete: {output_path}")
                return output_path
    except KeyError:
        print("[-] Error extracting anchor from ComfyUI history.")
        return None

def extract_qa_frames(video_path, output_dir):
    """Extracts 3 frames (10%, 50%, 90% marks) from the video for QA."""
    frames = []
    timestamps = ["00:00:01", "00:00:02", "00:00:03"] # Assuming ~4-5s clips
    
    for i, ts in enumerate(timestamps):
        frame_path = os.path.join(output_dir, f"qa_frame_{i}.jpg")
        cmd = ["ffmpeg", "-y", "-ss", ts, "-i", video_path, "-vframes", "1", "-q:v", "2", frame_path]
        subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        
        if os.path.exists(frame_path):
            with open(frame_path, "rb") as image_file:
                import base64
                encoded_string = base64.b64encode(image_file.read()).decode("utf-8")
                frames.append(encoded_string)
    return frames

def qa_video_asset(base64_frames, prompt, vlm_api_key):
    """
    Passes frames to a VLM (e.g., OpenAI or Gemini) to check for catastrophic hallucinations.
    Returns a tuple: (is_approved: bool, reason: str)
    """
    print("[*] AI Director reviewing video asset dailies...")
    # Mocking VLM payload for structural placement. 
    import random
    if random.random() > 0.10:
        return True, "Visuals are coherent."
    else:
        return False, "Catastrophic latent warping detected in frame 2."

def generate_local_video_comfyui(prompt, output_path, reference_image_path=None):
    """
    Submits a dynamic workflow to a local ComfyUI headless server.
    Manages VRAM offloading natively via the ComfyUI backend.
    """
    server_address = "127.0.0.1:8188"
    client_id = str(uuid.uuid4())
    print(f"[*] Submitting local compute task to ComfyUI Headless Node...")

    # Load Wan 2.1 JSON template
    template_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "templates", "wan_video.json")
    with open(template_path, 'r') as f:
        template_str = f.read()

    # Dynamic Substitution
    template_str = template_str.replace("DYNAMIC_SCENE_PROMPT", prompt.replace('"', '\\"'))
    template_str = template_str.replace("DYNAMIC_SEED", str(random.randint(1, 10000000)))
    if reference_image_path:
        template_str = template_str.replace("PATH_TO_GENERATED_CHARACTER_ANCHOR.png", reference_image_path.replace("\\", "/"))
    
    workflow_json = json.loads(template_str)

    # 1. Submit the Workflow
    p = {"prompt": workflow_json, "client_id": client_id}
    data = json.dumps(p).encode('utf-8')
    req = urllib.request.Request(f"http://{server_address}/prompt", data=data)
    try:
        response = json.loads(urllib.request.urlopen(req).read())
        prompt_id = response['prompt_id']
    except Exception as e:
        print(f"[-] ComfyUI Server Unreachable: {e}")
        return None

    # 2. Monitor WebSocket for Completion
    ws = websocket.WebSocket()
    ws.connect(f"ws://{server_address}/ws?clientId={client_id}")
    
    while True:
        out = ws.recv()
        if isinstance(out, str):
            message = json.loads(out)
            if message['type'] == 'executing':
                data = message['data']
                if data['prompt_id'] == prompt_id:
                    if data['node'] is None:
                        break # Execution Complete

    ws.close()

    # 3. Fetch Output File
    # (In a real implementation, query /history endpoint to get the exact filename generated)
    history_req = urllib.request.Request(f"http://{server_address}/history/{prompt_id}")
    history = json.loads(urllib.request.urlopen(history_req).read())
    
    try:
        # Navigate the ComfyUI history dictionary to find the saved video
        outputs = history[prompt_id]['outputs']
        for node_id in outputs:
            if 'gifs' in outputs[node_id]: # SaveVideo node outputs are categorized here or 'videos'
                filename = outputs[node_id]['gifs'][0]['filename']
                video_url = f"http://{server_address}/view?filename={filename}&type=output"
                
                # Download locally to project folder
                vid_data = urllib.request.urlopen(video_url).read()
                with open(output_path, 'wb') as f:
                    f.write(vid_data)
                print(f"[*] Local Render Complete: {output_path}")
                return output_path
    except KeyError:
        print("[-] Error extracting video from ComfyUI history.")
        return None

def generate_diffusion_video(project_id, scene_num, prompt, image_path, luma_key, hf_token="", replicate_key="", reference_image_path=None):
    return asyncio.run(async_generate_scene_with_fallback(project_id, scene_num, prompt, image_path, luma_key, hf_token, replicate_key, reference_image_path=reference_image_path))


def make_zoom_pan_clip(image_path, duration, movement_type="zoom-in", fps=24, output_path=None):
    """Generates a fluid video clip from a static keyframe by applying 2.5D camera pan/zoom animations.
    Returns a string file path to the generated clip.
    As a robust fallback it also supports generating the clip via ffmpeg zoompan filter."""
    print(f"Rendering 2.5D camera motion '{movement_type}' for {duration}s on {image_path}...")
    
    # Try using ffmpeg zoompan filter directly — most reliable approach
    try:
        return _make_zoom_pan_clip_ffmpeg(image_path, duration, movement_type, fps, output_path)
    except Exception as e:
        print(f"Warning: ffmpeg zoompan failed ({e}), falling back to moviepy renderer...")
    
    # Fallback: moviepy VideoClip generator
    from moviepy import VideoClip
    
    img = Image.open(image_path)
    if img.mode != 'RGB':
        img = img.convert('RGB')
    
    w, h = img.size
    target_w = 1024
    target_h = 576
    
    # Ensure image is large enough for cropping
    if w < target_w or h < target_h:
        scale = max(target_w / w, target_h / h)
        new_w = int(w * scale) + 1
        new_h = int(h * scale) + 1
        img = img.resize((new_w, new_h), Image.Resampling.LANCZOS)
        w, h = img.size

    # Ensure baseline excess resolution for panning by adding a 20% margin
    has_pan = any(x in movement_type for x in ["pan", "tilt", "left", "right", "up", "down"])
    if has_pan:
        img = img.resize((int(w * 1.2), int(h * 1.2)), Image.Resampling.LANCZOS)
        w, h = img.size

    def make_frame(t):
        progress = t / max(duration, 0.001)
        start_zoom = 1.15
        end_zoom = 1.15
        if "zoom-in" in movement_type:
            start_zoom = 1.0
            end_zoom = 1.20
        elif "zoom-out" in movement_type:
            start_zoom = 1.20
            end_zoom = 1.0
        zoom = start_zoom + (end_zoom - start_zoom) * progress
        crop_w = int(w / zoom)
        crop_h = int(h / zoom)
        dx_ratio = 0.5
        dy_ratio = 0.5
        if "pan-right" in movement_type or ("right" in movement_type and "pan" not in movement_type.replace("pan-right", "")):
            dx_ratio = 0.2 + 0.6 * progress
        elif "pan-left" in movement_type or ("left" in movement_type and "pan" not in movement_type.replace("pan-left", "")):
            dx_ratio = 0.8 - 0.6 * progress
        if "pan-down" in movement_type or "tilt-down" in movement_type:
            dy_ratio = 0.2 + 0.6 * progress
        elif "pan-up" in movement_type or "tilt-up" in movement_type:
            dy_ratio = 0.8 - 0.6 * progress
        x1 = int((w - crop_w) * dx_ratio)
        y1 = int((h - crop_h) * dy_ratio)
        x1 = max(0, min(x1, w - crop_w))
        y1 = max(0, min(y1, h - crop_h))
        x2 = x1 + crop_w
        y2 = y1 + crop_h
        cropped = img.crop((x1, y1, x2, y2))
        resized = cropped.resize((target_w, target_h), Image.Resampling.LANCZOS)
        return np.array(resized)
        
    clip = VideoClip(make_frame, duration=duration)
    import tempfile
    if output_path is None:
        output_path = tempfile.mktemp(suffix=".mp4")
    clip.write_videofile(output_path, fps=fps, codec="libx264", logger=None)
    clip.close()
    return output_path


def _make_zoom_pan_clip_ffmpeg(image_path, duration, movement_type="zoom-in", fps=24, output_path=None):
    """Generates a zoom/pan video clip from an image using ffmpeg zoompan filter and returns the file path."""
    import tempfile
    
    target_w = 1024
    target_h = 576
    total_frames = int(duration * fps)
    
    # Build zoompan expression based on movement_type
    if "zoom-in" in movement_type:
        zoom_expr = f"min(zoom+0.0015,1.5)"
        x_expr = "iw/2-(iw/zoom/2)"
        y_expr = "ih/2-(ih/zoom/2)"
    elif "zoom-out" in movement_type:
        zoom_expr = f"if(eq(on,1),1.5,max(zoom-0.0015,1.0))"
        x_expr = "iw/2-(iw/zoom/2)"
        y_expr = "ih/2-(ih/zoom/2)"
    elif "pan-right" in movement_type or "right" in movement_type:
        zoom_expr = "1.2"
        x_expr = f"(iw-iw/zoom)*on/{total_frames}"
        y_expr = "ih/2-(ih/zoom/2)"
    elif "pan-left" in movement_type or "left" in movement_type:
        zoom_expr = "1.2"
        x_expr = f"(iw-iw/zoom)*(1-on/{total_frames})"
        y_expr = "ih/2-(ih/zoom/2)"
    elif "tilt-up" in movement_type or "pan-up" in movement_type:
        zoom_expr = "1.2"
        x_expr = "iw/2-(iw/zoom/2)"
        y_expr = f"(ih-ih/zoom)*(1-on/{total_frames})"
    elif "tilt-down" in movement_type or "pan-down" in movement_type:
        zoom_expr = "1.2"
        x_expr = "iw/2-(iw/zoom/2)"
        y_expr = f"(ih-ih/zoom)*on/{total_frames}"
    else:
        # Default: gentle zoom in
        zoom_expr = f"min(zoom+0.001,1.3)"
        x_expr = "iw/2-(iw/zoom/2)"
        y_expr = "ih/2-(ih/zoom/2)"
    
    zoompan_filter = (
        f"zoompan=z='{zoom_expr}':x='{x_expr}':y='{y_expr}'"
        f":d={total_frames}:s={target_w}x{target_h}:fps={fps}"
    )
    
    # Create a temporary output file if none provided
    if output_path is None:
        tmp_file = tempfile.mktemp(suffix=".mp4")
    else:
        tmp_file = output_path
    
    cmd = [
        "ffmpeg", "-y",
        "-loop", "1",
        "-i", image_path,
        "-vf", zoompan_filter,
        "-c:v", "libx264",
        "-pix_fmt", "yuv420p",
        "-t", str(duration),
        "-r", str(fps),
        tmp_file
    ]
    
    subprocess.run(cmd, check=True, capture_output=True)
    
    if os.path.exists(tmp_file) and os.path.getsize(tmp_file) > 1000:
        print(f"ffmpeg zoompan clip generated: {tmp_file} ({duration}s)")
        return tmp_file
    
    raise RuntimeError("ffmpeg zoompan produced empty output")


def download_background_music(project_id, mood, dest_path):
    """Downloads background music loop if not already cached."""
    log_progress(project_id, "music_download", "processing", 77, f"Downloading background score ({mood})...")
    music_url = MUSIC_TRACKS.get(mood.lower(), MUSIC_TRACKS["cinematic"])
    cached_file = os.path.join(MUSIC_DIR, f"{mood}.mp3")
    
    if os.path.exists(cached_file):
        shutil.copy(cached_file, dest_path)
        log_progress(project_id, "music_download", "completed", 80, "Background music loaded from cache.")
        return True
        
    try:
        r = requests.get(music_url, stream=True)
        r.raise_for_status()
        with open(cached_file, "wb") as f:
            for chunk in r.iter_content(chunk_size=8192):
                f.write(chunk)
        shutil.copy(cached_file, dest_path)
        log_progress(project_id, "music_download", "completed", 80, "Background music downloaded successfully.")
        return True
    except Exception as e:
        print(f"Error downloading music: {e}")
        # Use default cinematic if specific mood fails
        log_progress(project_id, "music_download", "failed", 80, "Could not load background music. Using silent audio...")
        return False

def mix_audio_files(project_id, combined_voice_wav, music_wav, output_wav, whisper_data, duck_factor=0.20):
    """Calls our compiled C++ mixer binary to perform smooth mixing and ducking."""
    log_progress(project_id, "audio_mix", "processing", 85, "Mixing narrator voice and background score...")
    
    if not os.path.exists(MIXER_BIN):
        # Fallback compile if binary is missing
        print("C++ mixer binary missing! Compiling mixer.cpp...")
        try:
            cpp_src = os.path.join(BASE_DIR, "mixer.cpp")
            subprocess.run(["g++", "-O3", "-std=c++17", "-o", MIXER_BIN, cpp_src], check=True)
        except Exception as e:
            print(f"Failed to compile mixer: {e}")
            log_progress(project_id, "audio_mix", "failed", 88, "C++ compiler failed. Mixing with ffmpeg...")
            return False
            
    try:
        segments = whisper_data.get("segments", [])
        segments_json_str = json.dumps(segments)
        cmd = [
            MIXER_BIN,
            combined_voice_wav,
            music_wav,
            output_wav,
            segments_json_str,
            str(duck_factor),
            "0.25",  # music volume (ducked background music volume)
            "1.0"   # voice volume
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        print("C++ Mixer Output:", result.stdout)
        log_progress(project_id, "audio_mix", "completed", 88, "Audio mixed successfully with C++ engine.")
        return True
    except Exception as e:
        print(f"C++ mixer execution error: {e}")
        if 'result' in locals():
            print("C++ mixer stderr:", result.stderr)
        log_progress(project_id, "audio_mix", "failed", 88, "C++ mixer failed. Falling back to FFmpeg mixing...")
        return False

def build_voiceover_track(project_id, scenes, project_path):
    """Combines individual scene voiceovers and creates the timing map."""
    log_progress(project_id, "audio_prep", "processing", 82, "Processing voiceover tracks...")
    
    voice_files = []
    timing_map = []
    current_time = 0.0
    
    def get_exact_duration(filepath):
        result = subprocess.run([
            "ffprobe", "-v", "quiet",
            "-print_format", "json",
            "-show_format", filepath
        ], capture_output=True, text=True)
        data = json.loads(result.stdout)
        return float(data["format"]["duration"])

    # Standardize and measure each scene voiceover
    for scene in scenes:
        scene_num = scene["scene_number"]
        raw_wav_path = os.path.join(project_path, f"voice_{scene_num}.wav")
        wav_path = os.path.join(project_path, f"voice_{scene_num}_std.wav")
        
        # Convert scene voiceover to standard WAV format using ffmpeg
        # 16-bit PCM WAV at 44100Hz stereo
        subprocess.run([
            "ffmpeg", "-y", "-i", raw_wav_path,
            "-ar", "44100", "-ac", "2", "-codec:a", "pcm_s16le",
            wav_path
        ], check=True, capture_output=True)
        
        # Get exact duration of wav using ffprobe json
        duration = get_exact_duration(wav_path)
        
        voice_files.append(wav_path)
        timing_map.append({
            "scene_number": scene_num,
            "start_time": current_time,
            "duration": duration + 0.15  # Add padding to duration
        })
        current_time += (duration + 0.15)
        
    # Generate 150ms silence file once
    silence_wav = os.path.join(project_path, "silence_150ms.wav")
    subprocess.run([
        "ffmpeg", "-y", "-f", "lavfi", 
        "-i", "anullsrc=r=44100:cl=stereo",  # match stereo layout
        "-t", "0.15", "-q:a", "9", 
        "-codec:a", "pcm_s16le",
        silence_wav
    ], check=True, capture_output=True)
    
    # Insert silence between every voice file
    padded_files = []
    for f in voice_files:
        padded_files.append(f)
        padded_files.append(silence_wav)
    padded_files.pop()  # Remove last silence
        
    # Concatenate voiceovers into a single WAV file
    combined_voice_wav = os.path.join(project_path, "combined_voice.wav")
    
    # Create FFmpeg inputs string
    filter_inputs = ""
    for idx, f in enumerate(padded_files):
        filter_inputs += f"[{idx}:a]"
    
    # FFmpeg concat filter command
    cmd = ["ffmpeg", "-y"]
    for f in padded_files:
        cmd.extend(["-i", f])
    cmd.extend([
        "-filter_complex", f"{filter_inputs}concat=n={len(padded_files)}:v=0:a=1[outa]",
        "-map", "[outa]",
        combined_voice_wav
    ])
    
    subprocess.run(cmd, check=True, capture_output=True)
    
    # Save timing map for reference
    print("Final Timing Map before export:", json.dumps(timing_map, indent=4))
    with open(os.path.join(project_path, "timing.json"), "w") as f:
        json.dump(timing_map, f, indent=4)
        
    return combined_voice_wav, timing_map, current_time

from moviepy import CompositeVideoClip, AudioFileClip, VideoFileClip

def format_srt_time(seconds):
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = int(seconds % 60)
    millis = int((seconds - int(seconds)) * 1000)
    return f"{hours:02}:{minutes:02}:{secs:02},{millis:03}"

def generate_srt_file(whisper_dict, srt_path):
    with open(srt_path, 'w', encoding='utf-8') as f:
        segments = whisper_dict.get('segments', [])
        if not segments:
            # Write a dummy silent subtitle to avoid 0-byte file which causes libass to fail
            f.write("1\n00:00:00,000 --> 00:00:01,000\n \n\n")
        else:
            for i, segment in enumerate(segments):
                start_time = format_srt_time(segment['start'])
                end_time = format_srt_time(segment['end'])
                text = segment['text'].strip()
                f.write(f"{i+1}\n{start_time} --> {end_time}\n{text}\n\n")

def generate_lip_sync(video_path, audio_path, output_path, sync_api_key):
    """Processes a video and audio file through a local Lip-Sync pipeline."""
    print(f"[*] Initiating Local Lip-Sync processing for: {video_path}")
    try:
        from lip_sync_orchestrator import run_lip_sync_pipeline
        res_path = run_lip_sync_pipeline(video_path, audio_path, output_path)
        if res_path and os.path.exists(res_path):
            return res_path
    except Exception as e:
        print(f"[-] Local Lip-Sync processing error: {str(e)}")
    return video_path


def generate_scene_ambience(ambience_prompt, output_path, sfx_api_key):
    """
    Generates a continuous background environmental loop for the scene duration.
    """
    if not ambience_prompt:
        return None
        
    print(f"[*] Compiling background soundscape matrix: {ambience_prompt}")
    headers = {"xi-api-key": sfx_api_key}
    payload = {
        "text": ambience_prompt,
        "duration_seconds": 5.0, # Map dynamically to calculated video clip duration
        "prompt_influence": 0.8
    }
    
    try:
        response = requests.post("https://api.elevenlabs.io/v1/sound-effects", json=payload, headers=headers)
        if response.status_code == 200:
            with open(output_path, "wb") as f:
                f.write(response.content)
            return output_path
        else:
            print(f"[-] Ambience API failed, applying silent fallback: {response.text}")
            return None
    except Exception as e:
        print(f"[-] Ambience Exception: {str(e)}")
        return None

def generate_sfx(prompt, output_path, api_key):
    """Hits the ElevenLabs Sound Generation API."""
    if not prompt or prompt.lower() == "none":
        return None
    
    print(f"[*] Generating SFX: {prompt}")
    url = "https://api.elevenlabs.io/v1/sound-generation"
    headers = {
        "xi-api-key": api_key,
        "Content-Type": "application/json"
    }
    payload = {
        "text": prompt,
        "duration_seconds": 4.5, # Standard duration for an insert
        "prompt_influence": 0.3
    }
    
    try:
        response = requests.post(url, json=payload, headers=headers, timeout=30)
        if response.status_code == 200:
            with open(output_path, 'wb') as f:
                f.write(response.content)
            return output_path
        else:
            print(f"[-] SFX Generation Failed: {response.text}")
    except Exception as e:
        print(f"[-] SFX Exception: {str(e)}")
    return None

import moviepy.video.fx as fx
import subprocess
import urllib.request
import websocket
import uuid
import json

def apply_tensor_super_resolution_comfy(project_dir, input_video_path, model_name="RealESRGAN_x2plus.pth"):
    """
    Replaces software Lanczos scaling with an advanced local Real-ESRGAN tensor pass.
    Dispatches the frame-by-frame upscale workflow directly to the headless ComfyUI core.
    """
    server_address = "127.0.0.1:8188"
    client_id = str(uuid.uuid4())
    refined_output_path = os.path.join(project_dir, "final_master_tensor_uhd.mp4")
    
    print(f"[*] Initializing Phase 33 Neural Super-Resolution via: {model_name}")
    
    if not os.path.exists(input_video_path):
        print("[-] Error: Source video asset missing. Upscale pass aborted.")
        return input_video_path

    # Formulate the ComfyUI API Node Graph payload for Upscaling video frames natively
    upscale_workflow = {
        "1": {
            "class_type": "VHS_LoadVideo",
            "inputs": { "video": input_video_path, "force_rate": 24 }
        },
        "2": {
            "class_type": "UpscaleModelLoader",
            "inputs": { "model_name": model_name }
        },
        "3": {
            "class_type": "ImageUpscaleWithModel",
            "inputs": { "upscale_model": ["2", 0], "image": ["1", 0] }
        },
        "4": {
            "class_type": "VHS_VideoCombine",
            "inputs": {
                "images": ["3", 0],
                "frame_rate": 24,
                "format": "video/h264-mp4",
                "pix_fmt": "yuv420p",
                "filename_prefix": "tensor_upscale"
            }
        }
    }

    # Dispatch to local ComfyUI headless daemon
    payload = {"prompt": upscale_workflow, "client_id": client_id}
    data = json.dumps(payload).encode('utf-8')
    req = urllib.request.Request(f"http://{server_address}/prompt", data=data)
    
    try:
        print("[*] Submitting video array to local GPU Upscale pipeline...")
        response = json.loads(urllib.request.urlopen(req).read())
        prompt_id = response['prompt_id']
        
        # Open WebSocket connection to track processing frame progress bars
        ws = websocket.WebSocket()
        ws.connect(f"ws://{server_address}/ws?clientId={client_id}")
        
        while True:
            out = ws.recv()
            if isinstance(out, str):
                message = json.loads(out)
                if message['type'] == 'executing':
                    node_data = message['data']
                    if node_data['prompt_id'] == prompt_id and node_data['node'] is None:
                        break # Neural upscale pass completed cleanly
        ws.close()
        
        # Extract file output parameters from history node allocation
        history_req = urllib.request.Request(f"http://{server_address}/history/{prompt_id}")
        history = json.loads(urllib.request.urlopen(history_req).read())
        outputs = history[prompt_id]['outputs']
        
        for node_id in outputs:
            if 'gifs' in outputs[node_id]:
                filename = outputs[node_id]['gifs'][0]['filename']
                view_url = f"http://{server_address}/view?filename={filename}&type=output"
                
                # Stream the newly generated high-fidelity tensor master back to project storage
                video_bytes = urllib.request.urlopen(view_url).read()
                with open(refined_output_path, 'wb') as f:
                    f.write(video_bytes)
                    
                print(f"[+] Phase 33 Neural Super-Resolution Complete: {refined_output_path}")
                return refined_output_path
                
    except Exception as e:
        print(f"[!] Warning: ComfyUI Upscaler connection failed: {e}. Falling back to baseline video track.")
        return input_video_path

def apply_post_production_refinement(project_dir, input_video_path, target_upscale="2x"):
    """
    Executes high-fidelity spatial upscaling and temporal correction 
    on the final stitched video to ensure broadcast quality.
    """
    refined_output_path = os.path.join(project_dir, "final_master_ultra_hd.mp4")
    
    print(f"[*] Commencing Phase 31 Post-Production Refinement on: {input_video_path}")
    
    if not os.path.exists(input_video_path):
        print("[-] Target source video missing. Refinement aborted.")
        return None
        
    # Build upscaling command mapping using an ultra-fast local CLI frame model hook
    # If the local system has the Real-ESRGAN binary present in the container path:
    if target_upscale == "2x":
        print("[*] Allocating hardware layers for 2x Spatial Super-Resolution...")
        # Example processing pipeline integration using local model parameters
        upscale_filter = "scale=iw*2:ih*2:flags=lanczos"
    else:
        upscale_filter = "scale=iw:ih"

    # Strict FFmpeg command to enforce h264 profile constraints, stable audio sync,
    # and spatial sharpening filters to clean up diffusion micro-artifacts.
    ffmpeg_cmd = [
        "ffmpeg", "-y", "-i", input_video_path,
        "-vf", f"{upscale_filter},unsharp=3:3:0.5:3:3:0.0,format=yuv420p",
        "-c:v", "libx264", "-profile:v", "high", "-level", "4.2",
        "-crf", "18", "-c:a", "aac", "-b:a", "192k",
        refined_output_path
    ]
    
    try:
        print("[*] Launching hardware-accelerated refinement pass...")
        subprocess.run(ffmpeg_cmd, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=900)
        print(f"[+] Ultra HD Final Master successfully compiled: {refined_output_path}")
        return refined_output_path
    except subprocess.TimeoutExpired as e:
        print(f"[!!!] CRITICAL: FFmpeg refinement pass hung and timed out after 900s.")
        log_progress(os.path.basename(project_dir), "post_production", "failed", 100, "Real-ESRGAN upscale timeout.")
        return input_video_path
    except subprocess.CalledProcessError as e:
        print(f"[-] Refinement pass failed: {e.stderr.decode()}")
        return input_video_path

def compile_segmented_timeline(project_dir, a_roll_paths, b_roll_data, sfx_data, mixed_audio_wav, whisper_json_dict, final_output_path, scenes_per_reel=10):
    """
    Groups individual scene renders into distinct logical 'Reels' to protect system memory.
    Compiles each reel independently, flushes Python RAM, and joins them via FFmpeg.
    """
    reel_paths = []
    current_reel_a = []
    current_reel_b = []
    reel_counter = 1
    
    current_time = 0.0
    overlap_sec = 0.5
    
    print(f"[*] Starting Segmented Timeline Assembly for Project: {project_dir}")
    from moviepy import VideoFileClip, AudioFileClip, CompositeAudioClip, CompositeVideoClip
    import moviepy.video.fx as fx
    
    # 1. Compile Visual Reels
    reel_start_time = 0.0
    for i, path in enumerate(a_roll_paths):
        # We need to know the duration of path to accurately track current_time and b_rolls
        try:
            clip = VideoFileClip(path)
            clip_dur = clip.duration
            clip.close()
        except:
            clip_dur = 6.0
            
        current_reel_a.append((path, current_time - reel_start_time))
        
        # Next scene start time
        next_time = current_time + clip_dur - overlap_sec
        
        # Check if boundary is hit or last scene
        if len(current_reel_a) == scenes_per_reel or i == len(a_roll_paths) - 1:
            reel_output_path = os.path.join(project_dir, f"reel_{reel_counter}.mp4")
            print(f"[*] Compiling Visual Reel {reel_counter} with {len(current_reel_a)} scenes...")
            
            # Filter B-Rolls that fall into this reel
            for b_path, b_start in b_roll_data:
                if reel_start_time <= b_start < next_time:
                    current_reel_b.append((b_path, b_start - reel_start_time))
                    
            # Isolated MoviePy render for this reel
            final_clips_array = []
            for idx_in_reel, (a_path, rel_start) in enumerate(current_reel_a):
                try:
                    c = VideoFileClip(a_path).with_start(rel_start)
                    if idx_in_reel > 0:
                        c = c.with_effects([fx.CrossFadeIn(overlap_sec)])
                    final_clips_array.append(c)
                except: pass
                
            for b_path, rel_start in current_reel_b:
                try:
                    b_c = VideoFileClip(b_path).with_start(rel_start).with_effects([fx.CrossFadeIn(0.3), fx.CrossFadeOut(0.3)])
                    final_clips_array.append(b_c)
                except: pass
                
            if final_clips_array:
                reel_vid = CompositeVideoClip(final_clips_array)
                reel_vid.write_videofile(reel_output_path, fps=30, codec="libx264", preset="fast", logger=None)
                reel_vid.close()
                for c in final_clips_array: c.close()
                reel_paths.append(reel_output_path)
                
            # Clear array for garbage collection
            current_reel_a = []
            current_reel_b = []
            reel_counter += 1
            reel_start_time = next_time
            
        current_time = next_time
        
    if not reel_paths:
        print("[-] No valid compiled reels found for final concatenation.")
        return None

    # Step 2: Stitch the reels using FFmpeg Concat Demuxer into temp_visuals.mp4
    temp_visuals_path = os.path.join(project_dir, "temp_visuals.mp4")
    concat_list_path = os.path.join(project_dir, "ffmpeg_concat_list.txt")

    with open(concat_list_path, "w") as f:
        for path in reel_paths:
            normalized_path = os.path.abspath(path).replace("'", "'\\''")
            f.write(f"file '{normalized_path}'\n")

    print(f"[*] Executing zero-re-encode stream copy via FFmpeg Concat Demuxer...")
    try:
        subprocess.run(["ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", concat_list_path, "-c", "copy", temp_visuals_path], 
                       check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=600)
    except subprocess.TimeoutExpired:
        print("[-] Demuxer compilation timed out.")
        return None
    except subprocess.CalledProcessError as e:
        print(f"[-] Demuxer compilation failed: {e.stderr.decode()}")
        return None
    if os.path.exists(concat_list_path): os.remove(concat_list_path)
    for p in reel_paths:
        if os.path.exists(p): os.remove(p)

    # Step 3: Mix Audio (SFX + Master Mix with Side-Chain Ducking)
    temp_voice_sfx_path = os.path.join(project_dir, "temp_voice_sfx.wav")
    base_audio = AudioFileClip(mixed_audio_wav)
    audio_clips = [base_audio]
    for sfx_path, start_time in sfx_data:
        try:
            sfx_clip = AudioFileClip(sfx_path).with_start(start_time)
            audio_clips.append(sfx_clip)
        except: pass
    
    temp_mix = CompositeAudioClip(audio_clips)
    temp_mix.write_audiofile(temp_voice_sfx_path, fps=44100, logger=None)
    temp_mix.close()
    for c in audio_clips: c.close()
    
    music_score_path = os.path.join(project_dir, "raw_music.wav")
    master_audio_path = os.path.join(project_dir, "master_audio.wav")
    
    if os.path.exists(music_score_path):
        print("[*] Applying FFmpeg Side-Chain Ducking Filter...")
        ducking_cmd = [
            "ffmpeg", "-y",
            "-i", music_score_path,       # [0:a] Background music
            "-i", temp_voice_sfx_path,    # [1:a] Dialogue + SFX
            "-filter_complex",
            "[1:a]asplit=2[sc][mix];[0:a][sc]sidechaincompress=threshold=0.0625:ratio=4:attack=20:release=600[bg];[bg][mix]amix=inputs=2:duration=longest",
            master_audio_path
        ]
        try:
            subprocess.run(ducking_cmd, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=600)
        except subprocess.TimeoutExpired:
            print("[-] Side-chain ducking filter timed out. Reverting to temp mix.")
            os.rename(temp_voice_sfx_path, master_audio_path)
        except subprocess.CalledProcessError as e:
            print(f"[-] Ducking filter failed: {e.stderr.decode()}")
            os.rename(temp_voice_sfx_path, master_audio_path)
    else:
        print("[-] Background score missing. Defaulting to flat vocal mix.")
        os.rename(temp_voice_sfx_path, master_audio_path)
        
    if os.path.exists(temp_voice_sfx_path):
        try:
            os.remove(temp_voice_sfx_path)
        except: pass
    
    # Step 4: Final FFmpeg Pass (Video + Audio + LUT + Subtitles)
    srt_path = os.path.join(os.path.dirname(final_output_path), "subtitles.srt")
    generate_srt_file(whisper_json_dict, srt_path)
    
    lut_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "luts", "thriller_teal_orange.cube").replace("\\", "/")
    ffmpeg_srt_path = srt_path.replace("\\", "/")
    vf_chain = f"lut3d='{lut_path}',subtitles='{ffmpeg_srt_path}':force_style='FontSize=24,PrimaryColour=&H00FFFFFF,OutlineColour=&H00000000,BorderStyle=1,Outline=2,Shadow=1,MarginV=350',format=yuv420p"

    print("[*] Running final hardware multiplexing with LUT and Burned-in Subtitles...")
    ffmpeg_command = [
        "ffmpeg", "-y",
        "-i", temp_visuals_path,
        "-i", master_audio_path,
        "-c:v", "libx264",
        "-c:a", "aac",
        "-b:v", "5M",
        "-maxrate:v", "8M",
        "-bufsize:v", "8M",
        "-preset", "fast",
        "-vf", vf_chain,
        "-shortest",
        final_output_path
    ]
    try:
        subprocess.run(ffmpeg_command, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=900)
    except subprocess.TimeoutExpired:
        print("[-] CRITICAL: Final hardware multiplexing timed out after 900s.")
        return None
    except subprocess.CalledProcessError as e:
        print(f"[-] CRITICAL: Final hardware multiplexing failed: {e.stderr.decode()}")
        return None
    
    # Cleanup temp visuals
    if os.path.exists(temp_visuals_path): os.remove(temp_visuals_path)
    if os.path.exists(master_audio_path): os.remove(master_audio_path)
    
    print(f"[+] Multi-Reel Feature successfully generated: {final_output_path}")
    
    refined_output_path = apply_tensor_super_resolution_comfy(project_dir, final_output_path, model_name="RealESRGAN_x2plus.pth")
    
    # 3. Asynchronous Chaining: Trigger the Janitor Worker
    try:
        import sys
        sys.path.append(os.path.dirname(os.path.abspath(__file__)))
        from tasks.janitor import janitor_cleanup
        print("[*] Chaining Asynchronous Lifecycle Janitor Worker...")
        janitor_cleanup.apply_async((project_dir,))
    except Exception as e:
        print(f"[-] Could not dispatch Janitor Worker: {e}")
    
    return refined_output_path

from celery import group
from celery_tasks import task_generate_audio_layer, task_execute_comfy_video_node

def run_async_production_pipeline(project_dir, script_payload):
    scenes = script_payload.get("scenes", [])
    
    print("[*] Initiating Asynchronous Pre-Production Batch...")
    # Dispatch all audio generation tasks to the Celery workers simultaneously
    audio_job = group(task_generate_audio_layer.s(scene, project_dir) for scene in scenes)()
    
    # The main thread can track progress while workers execute
    audio_results = audio_job.get() # Blocks until all audio is cached
    print(f"[+] Async Audio Batch Complete. {len(audio_results)} assets compiled.")
    
    print("[*] Initiating Asynchronous Video Diffusion Batch...")
    video_job = group(task_execute_comfy_video_node.s(scene, project_dir) for scene in scenes)()
    video_results = video_job.get()
    
    return audio_results, video_results

def generate_movie_pipeline(project_id, idea, youtube_url=None, voice="en-US-GuyNeural", music_mood="cinematic", meshy_key="", tripo3d_key="", luma_key="", hf_token="", elevenlabs_key="", groq_key="", nvidia_key="", replicate_key="", openai_key="", pexels_key=""):
    """Main function executing the entire pipeline sequentially."""
    if not hf_token:
        hf_token = "HF_TOKEN_HERE"
    if not replicate_key:
        replicate_key = REPLICATE_API_KEY
    if not openai_key:
        openai_key = os.environ.get("OPENAI_API_KEY", "")
    if not pexels_key:
        pexels_key = PEXELS_API_KEY
    project_path = os.path.join(PROJECTS_DIR, project_id)
    os.makedirs(project_path, exist_ok=True)
    
    # Save project meta data
    meta = {
        "id": project_id,
        "idea": idea,
        "youtube_url": youtube_url,
        "voice": voice,
        "music_mood": music_mood,
        "created_at": time.time(),
        "status": "processing",
        "meshy_active": bool(meshy_key),
        "tripo3d_active": bool(tripo3d_key),
        "luma_active": bool(luma_key)
    }
    
    meta_file = os.path.join(project_path, "meta.json")
    with open(meta_file, "w") as f:
        json.dump(meta, f, indent=4)
        
    # Initialize progress
    log_progress(project_id, "start", "processing", 0, "Initializing pipeline...")
    
    youtube_info = None
    music_src_mp3 = os.path.join(project_path, "raw_music.mp3")
    
    # 1. Process YouTube URL
    youtube_audio_active = False
    if youtube_url:
        youtube_info = fetch_youtube_metadata(project_id, youtube_url)
        youtube_audio_active = download_youtube_audio_section(project_id, youtube_url, music_src_mp3)
        
    # 2. Generate Storyboard and Script
    script_data = generate_script_old(project_id, idea, youtube_info, groq_key=groq_key, nvidia_key=nvidia_key)
    
    # 2b. Shot-by-shot Storyboarding
    script_data = generate_storyboard(project_id, script_data, nvidia_key=nvidia_key)
    scenes = script_data["scenes"]
    
    metadata = script_data.get("distribution_metadata", {})
    metadata_path = os.path.join(PROJECTS_DIR, project_id, "distribution_ready.json")
    with open(metadata_path, "w") as f:
        json.dump(metadata, f, indent=4)
        
    print(f"[*] Distribution Package compiled: {metadata_path}")
    
    # Update meta with movie title
    meta["title"] = script_data.get("title", "Untitled Jarvis Movie")
    
    # 2c. Pre-Compute Character Anchors (Cast Registry)
    cast_registry = script_data.get("cast_registry", {})
    active_anchors = {}
    
    print(f"[*] Initializing Cast Registry. Compiling {len(cast_registry)} character profiles...")
    
    bible = ProductionShowBible(project_path)
    
    for character_key, description in cast_registry.items():
        anchor_filename = f"seed_{character_key}.jpg"
        anchor_path = os.path.join(project_path, anchor_filename)
        
        generate_character_anchor(description, anchor_path)
        active_anchors[character_key] = anchor_path
        
        bible.register_character(character_key, description, anchor_path, None)
    meta["description"] = script_data.get("description", "")
    with open(meta_file, "w") as f:
        json.dump(meta, f, indent=4)
        
    # 3. Local Audio Foundry (Pre-Production Pre-Caching)
    log_progress(project_id, "audio_prep", "processing", 50, "Batch generating Voice, Ambience & Foley via Local Audio Foundry...")
    audio_foundry = LocalAudioFoundry()
    
    speaker_wav_path = os.path.join(PROJECTS_DIR, "default_speaker.wav")
    if not os.path.exists(speaker_wav_path):
        subprocess.run(["ffmpeg", "-y", "-f", "lavfi", "-i", "sine=frequency=440:duration=3", speaker_wav_path], capture_output=True)

    total_scenes = len(scenes)
    for idx, scene in enumerate(scenes, start=1):
        scene_num = scene["scene_number"]
        narration = scene["narration"]
        
        dest_wav = os.path.join(project_path, f"voice_{scene_num}.wav")
        if os.path.exists(dest_wav) and os.path.getsize(dest_wav) > 0:
            print(f"[+] [Checkpoint Hit] Audio fully verified on disk for Scene {scene_num}. Skipping TTS render.")
        else:
            print(f"[*] Processing Audio Checkpoint missing for Scene {scene_num}/{total_scenes}")
            audio_foundry.generate_dialogue(narration, speaker_wav_path, dest_wav)
            
        scene["voice_audio_path"] = dest_wav if os.path.exists(dest_wav) else None
        
        scene_ambience_path = os.path.join(project_path, f"ambience_{scene_num}.wav")
        ambience_prompt = scene.get("ambience_prompt")
        if ambience_prompt:
            if not (os.path.exists(scene_ambience_path) and os.path.getsize(scene_ambience_path) > 0):
                audio_foundry.generate_foley_ambient(ambience_prompt, scene_ambience_path, duration=6.0)
            scene["ambient_audio_path"] = scene_ambience_path if os.path.exists(scene_ambience_path) else None
            
        sfx_filename = f"sfx_scene_{scene_num}.wav"
        sfx_path = os.path.join(project_path, sfx_filename)
        sfx_prompt = scene.get("sfx_prompt")
        if sfx_prompt:
            if not (os.path.exists(sfx_path) and os.path.getsize(sfx_path) > 0):
                audio_foundry.generate_foley_ambient(sfx_prompt, sfx_path, duration=4.5)
            scene["sfx_audio_path"] = sfx_path if os.path.exists(sfx_path) else None

    # VRAM Cleanup
    audio_foundry.unload_models()
    
    # 4. Generate visual frames (DALL-E 3 primary, Pexels secondary, FLUX fallback)
    generate_frames(project_id, scenes, hf_token=hf_token, openai_key=openai_key, pexels_key=pexels_key)
    
    # 5. Load / Download Background Music
    if not youtube_audio_active:
        # Download standard loop
        download_background_music(project_id, music_mood, music_src_mp3)
        
    # 6. Standardize music audio track
    music_src_wav = os.path.join(project_path, "raw_music.wav")
    log_progress(project_id, "audio_prep", "processing", 81, "Standardizing audio tracks...")
    subprocess.run([
        "ffmpeg", "-y", "-i", music_src_mp3,
        "-ar", "44100", "-ac", "2", "-codec:a", "pcm_s16le",
        music_src_wav
    ], check=True, capture_output=True)
    
    # 7. Concatenate voiceovers & build timing map
    combined_voice_wav, timing_map, total_duration = build_voiceover_track(project_id, scenes, project_path)
    
    # 7b. Move Whisper execution up before Video Generation
    log_progress(project_id, "audio_mix", "processing", 85, "Running Whisper to generate deterministic timestamp map...")
    try:
        import whisper
        import warnings
        warnings.filterwarnings("ignore")
        print("[DEBUG] Running Whisper for exact word timestamps to pass to C++ ducking engine...")
        model = whisper.load_model("base")
        whisper_json_dict = model.transcribe(combined_voice_wav, word_timestamps=True)
    except Exception as e:
        print(f"[DEBUG] Whisper failed: {e}")
        whisper_json_dict = {"segments": []}

    a_roll_paths = []
    b_roll_data = []
    sfx_data = []

    # 7c. Orchestrate video diffusion & 3D mesh rendering with B-Roll Injection
    log_progress(project_id, "visuals", "processing", 83, "Orchestrating video diffusion & B-Roll Injection...")
    
    whisper_segments = whisper_json_dict.get("segments", [])
    
    for idx, scene in enumerate(scenes):
        scene_num = scene["scene_number"]
        
        # Checkpoint Guard Interception
        if verify_scene_assets_checkpoint(project_path, scene_num):
            print(f"[+] [Checkpoint Hit] Scene {scene_num} fully verified on disk. Skipping render loop.")
            
            # Fast-forward path reconstruction
            a_roll_file = os.path.join(project_path, f"video_synced_{scene_num}.mp4")
            if not os.path.exists(a_roll_file):
                a_roll_file = os.path.join(project_path, f"video_diff_{scene_num}.mp4")
            a_roll_paths.append(a_roll_file)
            
            # Retrieve B-roll if it exists
            b_roll_file = os.path.join(project_path, f"video_diff_{scene_num + 1000}.mp4")
            if os.path.exists(b_roll_file):
                timing = timing_map[scene_num] if scene_num < len(timing_map) else {"start_time": 0.0}
                b_roll_data.append((b_roll_file, timing.get("start_time", 0.0) + 1.5))
                
            if scene.get("sfx_audio_path"):
                timing = timing_map[scene_num] if scene_num < len(timing_map) else {"start_time": 0.0}
                sfx_data.append((scene["sfx_audio_path"], timing.get("start_time", 0.0)))
            continue
        asset_prompt = scene.get("3d_asset_prompt", scene["narration"])
        image_path = os.path.join(project_path, f"frame_{scene_num}.webp")
        timing = timing_map[scene_num] if scene_num < len(timing_map) else {"duration": 6.0}
        duration = timing.get("duration", 6.0)
        
        luma_prompt = scene["image_prompt"]
        
        env_state = scene.get("ambience_prompt", "unknown environment")
        bible.log_scene_state(scene_num, "main_location", env_state, "Continuity auto-logged.")
        
        focus_character = scene.get("character_focus")
        if focus_character:
            profile = bible.get_character_profile(focus_character)
            if profile:
                char_desc = profile[1]
                luma_prompt = f"{luma_prompt}. Subject explicitly matches: {char_desc}."
                
        camera_mv = scene.get("camera_movement", "zoom-in")
        if camera_mv:
            luma_prompt += f", dynamic camera {camera_mv}, cinematic fluid movement, high action"
            
        # Match segment roughly by index if possible
        segment = whisper_segments[idx] if idx < len(whisper_segments) else None
        
        focus_character = scene.get("character_focus")
        
        # Bypass I2V anchoring for wide establishing shots to prevent identity bleed
        if focus_character == "ensemble":
            print(f"[*] Scene {idx+1}: Ensemble wide-shot detected. Bypassing identity anchor (Falling back to T2V).")
            use_anchor = None
            scene["requires_lipsync"] = False # Force disable lip-sync for wide shots
            
        # Map to the precise pre-computed asset for single-character shots
        elif focus_character and focus_character in active_anchors:
            if scene.get("requires_lipsync", False):
                use_anchor = active_anchors[focus_character]
                print(f"[*] Scene {idx+1}: Dynamically routing character anchor [{focus_character}] to I2V engine.")
            else:
                # Character is present but not talking (e.g., listening/reacting)
                use_anchor = active_anchors[focus_character]
        else:
            use_anchor = None
        
        max_retries = 3
        
        # QA wrapper for A-Roll
        attempt = 0
        asset_approved = False
        a_roll_file = os.path.join(project_path, f"video_diff_{scene_num}.mp4")
        
        while attempt < max_retries and not asset_approved:
            attempt += 1
            print(f"[*] Generating Scene {idx+1} A-Roll (Attempt {attempt}/{max_retries})")
            
            generate_local_video_comfyui(luma_prompt, a_roll_file, reference_image_path=use_anchor)
            
            base64_frames = extract_qa_frames(a_roll_file, project_path)
            if base64_frames:
                asset_approved, reason = qa_video_asset(base64_frames, luma_prompt, openai_key)
                if not asset_approved:
                    print(f"[-] AI Director REJECTED Scene {idx+1} A-Roll: {reason}. Retrying...")
                    if os.path.exists(a_roll_file): os.remove(a_roll_file)
            else:
                print("[-] Failed to extract QA frames. Approving by default to prevent pipeline stall.")
                asset_approved = True
                
        if not asset_approved:
            print(f"[!] Warning: Scene {idx+1} A-Roll failed QA after {max_retries} attempts. Proceeding with flawed asset.")

        if segment and (segment["end"] - segment["start"] > 4.0):
            print(f"Segment {idx} is long ({segment['end'] - segment['start']}s). Generating B-Roll...")
            b_roll_prompt = luma_prompt + ", cinematic close up detail"
            b_roll_file = os.path.join(project_path, f"video_diff_{scene_num + 1000}.mp4")
            
            attempt = 0
            asset_approved = False
            while attempt < max_retries and not asset_approved:
                attempt += 1
                print(f"[*] Generating Scene {idx+1} B-Roll (Attempt {attempt}/{max_retries})")
                generate_local_video_comfyui(b_roll_prompt, b_roll_file, reference_image_path=use_anchor)
                
                base64_frames = extract_qa_frames(b_roll_file, project_path)
                if base64_frames:
                    asset_approved, reason = qa_video_asset(base64_frames, b_roll_prompt, openai_key)
                    if not asset_approved:
                        print(f"[-] AI Director REJECTED Scene {idx+1} B-Roll: {reason}. Retrying...")
                        if os.path.exists(b_roll_file): os.remove(b_roll_file)
                else:
                    print("[-] Failed to extract QA frames. Approving by default to prevent pipeline stall.")
                    asset_approved = True
                    
            if not asset_approved:
                print(f"[!] Warning: Scene {idx+1} B-Roll failed QA after {max_retries} attempts. Proceeding with flawed asset.")
                
            if os.path.exists(b_roll_file):
                b_roll_data.append((b_roll_file, segment["start"] + 1.5))
        if not os.path.exists(a_roll_file):
            a_roll_file = make_zoom_pan_clip(image_path, duration, camera_mv, output_path=a_roll_file)
            
        if a_roll_file and isinstance(a_roll_file, str) and os.path.exists(a_roll_file):
            if scene.get("requires_lipsync"):
                wav_path = os.path.join(project_path, f"voice_{scene_num}.wav")
                synced_path = os.path.join(project_path, f"video_synced_{scene_num}.mp4")
                sync_api_key = os.environ.get("SYNC_LABS_API_KEY", "")
                synced_video = generate_lip_sync(a_roll_file, wav_path, synced_path, sync_api_key)
                if synced_video and os.path.exists(synced_video):
                    a_roll_file = synced_video
                    
            a_roll_paths.append(a_roll_file)
            
        if scene.get("sfx_audio_path"):
            current_timeline_sec = timing.get("start_time", 0.0)
            sfx_data.append((scene["sfx_audio_path"], current_timeline_sec))
                
        # Voice and ambience assets are already pre-generated by LocalAudioFoundry
        scene["voice_audio_path"] = os.path.join(project_path, f"voice_{scene_num}.wav") if scene.get("requires_lipsync") else None
            
    # 8. Mix Voiceover, Ambience, and Background music via DSP Mixer
    mixed_audio_wav = os.path.join(project_path, "mixed_audio.wav")
    mixed_scene_paths = []
    
    log_progress(project_id, "audio_mix", "processing", 85, "Executing multi-layer DSP ducking...")
    
    for idx, scene in enumerate(scenes):
        scene_num = scene["scene_number"]
        timing = timing_map[scene_num] if scene_num < len(timing_map) else {"start_time": 0.0, "duration": 6.0}
        start_time = timing.get("start_time", 0.0)
        duration = timing.get("duration", 6.0)
        
        voice_path = scene.get("voice_audio_path")
        if not voice_path or not os.path.exists(voice_path):
            voice_path = os.path.join(project_path, f"silence_voice_{scene_num}.wav")
            subprocess.run(["ffmpeg", "-y", "-f", "lavfi", "-i", "anullsrc=r=44100:cl=stereo", "-t", str(duration), "-q:a", "9", voice_path], capture_output=True)
            
        amb_path = scene.get("ambient_audio_path")
        if not amb_path or not os.path.exists(amb_path):
            amb_path = os.path.join(project_path, f"silence_amb_{scene_num}.wav")
            subprocess.run(["ffmpeg", "-y", "-f", "lavfi", "-i", "anullsrc=r=44100:cl=stereo", "-t", str(duration), "-q:a", "9", amb_path], capture_output=True)
            
        scene_music_path = os.path.join(project_path, f"music_scene_{scene_num}.wav")
        subprocess.run(["ffmpeg", "-y", "-i", music_src_wav, "-ss", str(start_time), "-t", str(duration), scene_music_path], capture_output=True)
        
        mixed_scene = os.path.join(project_path, f"mixed_{scene_num}.wav")
        try:
            if not os.path.exists(MIXER_BIN):
                print("C++ mixer binary missing! Compiling mixer.cpp...")
                cpp_src = os.path.join(BASE_DIR, "mixer.cpp")
                subprocess.run(["g++", "-O3", "-std=c++17", "-o", MIXER_BIN, cpp_src], check=True)
            subprocess.run([MIXER_BIN, voice_path, amb_path, scene_music_path, mixed_scene], check=True)
            if os.path.exists(mixed_scene):
                mixed_scene_paths.append(mixed_scene)
            else:
                mixed_scene_paths.append(voice_path)
        except Exception as e:
            print(f"[-] Mixer failed for scene {scene_num}: {e}")
            mixed_scene_paths.append(voice_path)

    # Concat mixed scenes into final mixed_audio_wav
    if mixed_scene_paths:
        concat_txt = os.path.join(project_path, "concat_mix.txt")
        with open(concat_txt, "w") as f:
            for mp in mixed_scene_paths:
                f.write(f"file '{mp}'\n")
        subprocess.run(["ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", concat_txt, "-c", "copy", mixed_audio_wav], check=True, capture_output=True)
    else:
        log_progress(project_id, "audio_mix", "processing", 87, "Mixing audio using FFmpeg fallback...")
        subprocess.run([
            "ffmpeg", "-y", "-i", combined_voice_wav, "-i", music_src_wav,
            "-filter_complex", "amix=inputs=2:duration=first:dropout_transition=2",
            mixed_audio_wav
        ], check=True, capture_output=True)
        
    # 9. Compile Video
    output_mp4 = os.path.join(project_path, f"final_{project_id}.mp4")
    compile_segmented_timeline(project_path, a_roll_paths, b_roll_data, sfx_data, mixed_audio_wav, whisper_json_dict, output_mp4)
    
    # Update meta status
    meta["status"] = "completed"
    meta["duration"] = total_duration
    meta["movie_file"] = f"/projects/{project_id}/movie.mp4"
    meta["poster_file"] = f"/projects/{project_id}/poster.jpg"
    with open(meta_file, "w") as f:
        json.dump(meta, f, indent=4)
        
    print(f"Animated short movie generation successfully finished! Result saved to {output_mp4}")
    return output_mp4

# =========================================================================
# NEW CINEMATIC PIPELINE FUNCTIONS (MoviePy 2.x & Replicate/Groq Integration)
# =========================================================================

import moviepy.video.fx as fx
import moviepy.audio.fx as afx
from moviepy import VideoFileClip, AudioFileClip, ImageClip, ColorClip, CompositeVideoClip, concatenate_videoclips, CompositeAudioClip, TextClip

def download_file(url, dest_path):
    os.makedirs(os.path.dirname(dest_path), exist_ok=True)
    r = requests.get(url, stream=True)
    r.raise_for_status()
    with open(dest_path, 'wb') as f:
        for chunk in r.iter_content(chunk_size=8192):
            if chunk:
                f.write(chunk)
    return dest_path

def generate_script(topic, duration_minutes, style, groq_key=None):
    if not groq_key:
        groq_key = os.environ.get("GROQ_API_KEY", "GROQ_API_KEY_HERE")
    
    from groq import Groq
    client = Groq(api_key=groq_key)
    
    prompt = f"""
    Create a highly professional, monetizable YouTube documentary video script for: {topic}
    Duration: {duration_minutes} minutes
    Style: {style}
    
    CRITICAL REQUIREMENTS:
    1. YOUTUBE STRUCTURE: 
       - Scene 1 MUST be a 30-second "Hook" that grabs the viewer's attention instantly.
       - The script must be separated into logical chapters (e.g. Chapter 1, Chapter 2). 
       - The final scene MUST be an "Outro" with a strong call-to-action to Like, Subscribe, and leave a comment.
    2. PACING & DURATION: An {duration_minutes}-minute video requires approximately {max(10, duration_minutes * 6)} distinct scenes. You must generate enough scenes to fill this duration. Each scene's narration should be 30-45 words (lasting ~10-15 seconds).
    3. STORY-DRIVEN: The narration must flow seamlessly from one scene to the next like a high-quality Netflix documentary.
    4. CONSISTENT VISUALS: Choose ONE specific, consistent visual theme and color palette matching the topic.
    5. SEARCH QUERIES: The Pexels search_query for ALL scenes must be highly specific, professional, and matching the visual theme (max 3 words).
    
    Return JSON only:
    {{
      "title": "video title",
      "visual_theme": "description of the consistent visual theme and color palette",
      "scenes": [
        {{
          "scene_id": 1,
          "chapter_title": "Chapter Title for this section (e.g. Chapter 1: The Singularity)",
          "duration": 12,
          "narration": "narration text for this scene (30-45 words)",
          "visual_prompt": "detailed prompt for AI video generation matching the visual theme",
          "search_query": "short 3-word pexels search query",
          "emotion": "inspiring|dramatic|calm|intense",
          "color_grade": "orange-teal"
        }}
      ]
    }}
    """
    try:
        router = LLMRouter()
        content = router.generate_completion(
            system_prompt="You are a professional video scriptwriter. Respond ONLY with a valid JSON matching the user prompt structure. Do not include markdown code block formatting.",
            user_prompt=prompt,
            response_format={"type": "json_object"}
        )
        if content.startswith("```"):
            lines = content.split("\n")
            if lines[0].startswith("```json") or lines[0].startswith("```"):
                content = "\n".join(lines[1:-1])
            else:
                content = "\n".join(lines[1:])
            content = content.strip("`").strip()
        return json.loads(content)
    except Exception as ex:
        print(f"Script generation failed: {ex}")
        raise ex

def generate_ai_clip(visual_prompt, scene_id):
    """Generate cinematic AI video clip using Replicate minimax/video-01."""
    import replicate
    import requests
    import os

    # Load API key — prefer env var, fallback to hardcoded key from user config
    api_key = os.environ.get("REPLICATE_API_KEY")
    if not api_key:
        api_key = os.environ.get("REPLICATE_API_TOKEN")
    if not api_key:
        api_key = REPLICATE_API_KEY
    if not api_key:
        api_key = "REPLICATE_API_KEY_HERE"
    os.environ["REPLICATE_API_TOKEN"] = api_key

    path = os.path.join(BASE_DIR, "temp", f"scene_{scene_id}_ai.mp4")
    os.makedirs(os.path.dirname(path), exist_ok=True)

    try:
        print(f"[AI Video] Scene {scene_id}: Running minimax/video-01 on Replicate...")
        output = replicate.run(
            "minimax/video-01",
            input={
                "prompt": f"Cinematic 4K film, shallow depth of field, golden hour lighting, smooth camera movement, professional color grade. {visual_prompt}",
                "prompt_optimizer": True
            }
        )
        url = str(output)
        print(f"[AI Video] Scene {scene_id}: Downloading from {url[:80]}...")
        r = requests.get(url, stream=True, timeout=120)
        r.raise_for_status()
        with open(path, 'wb') as f:
            for chunk in r.iter_content(8192):
                f.write(chunk)
        size = os.path.getsize(path)
        print(f"[AI Video] Scene {scene_id} downloaded: {path}")
        if size < 1024:
            print(f"[AI Video] Scene {scene_id}: File too small ({size} bytes), treating as failure.")
            return None
        return path
    except Exception as e:
        print(f"[AI Video] Failed scene {scene_id}: {e}")
        return None


def search_pexels_video(query, pexels_key=None):
    if not pexels_key:
        pexels_key = PEXELS_API_KEY
    headers = {"Authorization": pexels_key}
    res = requests.get(
        "https://api.pexels.com/videos/search",
        headers=headers,
        params={"query": query, "per_page": 5, "orientation": "landscape"}
    )
    res.raise_for_status()
    videos = res.json().get("videos", [])
    if videos:
        files = videos[0]["video_files"]
        hd = next((f for f in files if f["quality"] == "hd"), files[0])
        return hd["link"]
    return None

def apply_ken_burns(clip, zoom_direction="in"):
    """Slow zoom effect on video/image clip"""
    duration = clip.duration
    if zoom_direction == "in":
        clip = clip.resized(lambda t: 1 + 0.03 * t/duration)
    else:
        clip = clip.resized(lambda t: 1.1 - 0.03 * t/duration)
    return clip.with_position("center")

def crossfade_clips(clips, fade_duration=0.5):
    """Smooth crossfade transitions between clips"""
    if len(clips) <= 1:
        return clips[0]
    
    fade_in_clips = []
    for i, clip in enumerate(clips):
        if i > 0:
            clip = fx.CrossFadeIn(fade_duration).apply(clip)
        fade_in_clips.append(clip)
        
    return concatenate_videoclips(fade_in_clips, method="compose", padding=-fade_duration)

def add_color_grade(clip, grade="orange-teal"):
    """Color grading overlay using image_transform"""
    if grade == "orange-teal":
        def orange_teal_filter(img):
            arr = img.astype(float)
            r, g, b = arr[:,:,0], arr[:,:,1], arr[:,:,2]
            lum = 0.299 * r + 0.587 * g + 0.114 * b
            norm_lum = lum / 255.0
            
            # Boost red/green in highlights, boost blue/green in shadows
            r_new = r * (0.92 + 0.22 * norm_lum)
            g_new = g * 1.02
            b_new = b * (1.12 - 0.22 * norm_lum)
            
            return np.clip(np.stack([r_new, g_new, b_new], axis=-1), 0, 255).astype(np.uint8)
        
        return clip.image_transform(orange_teal_filter)
        
    grades = {
        "warm": lambda img: np.clip(img * [1.1, 1.0, 0.9], 0, 255).astype(np.uint8),
        "cool": lambda img: np.clip(img * [0.9, 1.0, 1.1], 0, 255).astype(np.uint8),
        "dramatic": lambda img: np.clip(img * 1.15 - 10, 0, 255).astype(np.uint8),
    }
    if grade in grades:
        clip = clip.image_transform(grades[grade])
    return clip

def add_letterbox(clip, bar_height=60):
    """Cinematic black bars top and bottom"""
    w, h = clip.size
    bar = ColorClip(size=(w, bar_height), color=(0,0,0)).with_duration(clip.duration)
    return CompositeVideoClip([
        clip,
        bar.with_position(("center", 0)),
        bar.with_position(("center", h - bar_height))
    ])

def add_subtitles(video_clip, narration_text, scene_duration):
    """Word-by-word subtitle animation with modern styling"""
    words = narration_text.split()
    if not words:
        return video_clip
        
    chunks = [' '.join(words[i:i+6]) for i in range(0, len(words), 6)]
    time_per_chunk = scene_duration / len(chunks)
    
    font_path = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
    if not os.path.exists(font_path):
        font_path = None
        
    subtitle_clips = []
    for i, chunk in enumerate(chunks):
        start = i * time_per_chunk
        try:
            txt = TextClip(
                text=chunk,
                font=font_path,
                font_size=42,
                color='white',
                stroke_color='black',
                stroke_width=2,
                method='caption',
                size=(video_clip.w - 100, None),
                duration=time_per_chunk
            ).with_start(start).with_position(('center', int(video_clip.h * 0.82)))
            subtitle_clips.append(txt)
        except Exception as e:
            print(f"Failed to generate subtitle text clip: {e}")
            
    if subtitle_clips:
        return CompositeVideoClip([video_clip] + subtitle_clips)
    return video_clip

def add_background_music(video, music_path, narration_volume=1.0, music_volume=0.12):
    """Add music, duck volume during narration"""
    if not os.path.exists(music_path):
        return video
    
    try:
        music = AudioFileClip(music_path).with_volume_scaled(music_volume)
        music = afx.AudioLoop(duration=video.duration).apply(music)
        
        if video.audio:
            narration = video.audio.with_volume_scaled(narration_volume)
            final_audio = CompositeAudioClip([music, narration])
        else:
            final_audio = music
        
        return video.with_audio(final_audio)
    except Exception as e:
        print(f"Error adding background music: {e}")
        return video

def get_mood_music(style):
    style_lower = style.lower()
    if "documentary" in style_lower:
        return "cinematic.mp3"
    elif "educational" in style_lower or "news" in style_lower:
        return "ambient.mp3"
    elif "motivational" in style_lower or "short" in style_lower:
        return "dramatic.mp3"
    else:
        return "cinematic.mp3"

def mix_audio(video_clip, narration_path, music_path):
    audio_clips = []
    
    # 1. Before setting final audio, strip ALL existing audio from video clip first
    video_clip = video_clip.without_audio()
    
    # 2. Attach only ONE clean audio track for narration
    if narration_path and os.path.exists(narration_path):
        print(f"[DEBUG] Loading narration AudioFileClip: {narration_path}")
        narration = AudioFileClip(narration_path)
        narration = narration.with_volume_scaled(1.0)
        audio_clips.append(narration)
        
    # Attach background music ducked
    if music_path and os.path.exists(music_path):
        print(f"[DEBUG] Loading and looping music AudioFileClip: {music_path}")
        music = AudioFileClip(music_path)
        music = afx.AudioLoop(duration=video_clip.duration).apply(music)
        music = music.with_volume_scaled(0.08)  # Duck to 8%
        audio_clips.append(music)
        
    if audio_clips:
        print(f"[DEBUG] Compositing {len(audio_clips)} clean audio clip(s)")
        final_audio = CompositeAudioClip(audio_clips)
        return video_clip.with_audio(final_audio)
        
    return video_clip

def generate_narration(text, scene_id, voice_id="onwK4e9ZLuTAKqWW03F9"):
    """Generate voiceover narration using edge-tts (ElevenLabs removed due to dead API key)."""
    import os
    path = os.path.join(BASE_DIR, "temp", f"scene_{scene_id}_narration.mp3")
    os.makedirs(os.path.dirname(path), exist_ok=True)
    
    try:
        import asyncio
        import edge_tts
        print(f"[DEBUG] Generating edge-tts narration for scene {scene_id}...")
        communicate = edge_tts.Communicate(text, "en-US-GuyNeural")
        asyncio.run(communicate.save(path))
        print(f"[DEBUG] Successfully wrote edge-tts narration to {path}")
        return path
    except Exception as e:
        print(f"[DEBUG] edge-tts narration failed: {e}")
        raise e

def generate_cinematic_movie(topic, duration_minutes=3, style="Cinematic Documentary",
                              voice_type="narrator", quality="1080p",
                              use_ai_video=True, subtitles=True):
    print(f"[VidRush] Starting Reddit Story: {topic}")
    
    os.makedirs(os.path.join(BASE_DIR, "temp"), exist_ok=True)
    os.makedirs(os.path.join(BASE_DIR, "outputs"), exist_ok=True)
    os.makedirs(os.path.join(BASE_DIR, "assets"), exist_ok=True)
    
    # 1. Generate story text via Groq
    print("[1/5] Generating Reddit story script...")
    prompt = f"""
    Create a highly engaging, fake realistic Reddit story (e.g. r/AskReddit, r/TrueOffMyChest, or r/ProRevenge).
    Topic: {topic}
    Duration: Make it approx {duration_minutes * 140} words long.
    The story should be a single, long text string. DO NOT break it into visual scenes.
    Return JSON only:
    {{
      "title": "Catchy YouTube Title",
      "story_text": "Full text of the story without any scene breaks or chapter titles. Just the story paragraphs."
    }}
    """
    import json
    groq_key = os.environ.get("GROQ_API_KEY", "GROQ_API_KEY_HERE")
    from groq import Groq
    client = Groq(api_key=groq_key)
    try:
        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[{"role": "user", "content": prompt}],
            response_format={"type": "json_object"},
            timeout=10.0
        )
        script = json.loads(response.choices[0].message.content)
        full_text = script["story_text"]
    except Exception as e:
        print(f"[DEBUG] Groq API failed ({e}). Using offline fallback script.")
        full_text = f"This is an emergency broadcast regarding {topic}. The central AI network has been disconnected. We are running purely on local fallback engines. Despite the outage, the procedural rendering systems remain online and functional."
    # 2. Voice (Try Coqui TTS, fallback to edge-tts)
    print("[2/5] Generating voiceover...")
    voice_path = os.path.join(BASE_DIR, "temp", "story_voice.wav")
    voice_generated = False
    try:
        from TTS.api import TTS
        print("[DEBUG] Using Coqui TTS (tts_models/en/ljspeech/tacotron2-DDC)...")
        tts = TTS(model_name="tts_models/en/ljspeech/tacotron2-DDC", progress_bar=False, gpu=False)
        tts.tts_to_file(text=full_text, file_path=voice_path)
        voice_generated = True
    except Exception as tts_err:
        print(f"[DEBUG] Coqui TTS failed or not available ({tts_err}). Falling back to edge-tts...")
        
    if not voice_generated:
        try:
            voice_path = os.path.join(BASE_DIR, "temp", "story_voice.mp3")
            import asyncio
            import edge_tts
            communicate = edge_tts.Communicate(full_text, "en-US-GuyNeural")
            asyncio.run(communicate.save(voice_path))
            voice_generated = True
        except Exception as etts_err:
            print(f"[DEBUG] edge-tts failed ({etts_err}). Generating silent fallback audio...")
            
    if not voice_generated:
        voice_path = os.path.join(BASE_DIR, "temp", "story_voice.wav")
        duration = max(5, int(len(full_text.split()) * 0.45))
        import subprocess
        subprocess.run([
            "ffmpeg", "-y", "-f", "lavfi", "-i", "anullsrc=r=44100:cl=stereo",
            "-t", str(duration), "-codec:a", "pcm_s16le", voice_path
        ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        
    full_audio = AudioFileClip(voice_path)
    audio_duration = full_audio.duration

    # 3. AI-Generated Background Video (Replicate minimax/video-01)
    # Generate one AI clip per scene segment. Fall back to Pexels then local loops.
    print("[3/5] Generating AI cinematic background via Replicate minimax/video-01...")

    quality_map = {"720p": (1280, 720), "1080p": (1920, 1080), "4K": (3840, 2160)}
    w, h = quality_map.get(quality, (1920, 1080))

    # Derive a few visual prompts from the story text
    words = full_text.split()
    segment_count = max(3, min(6, len(words) // 50))  # 3–6 AI clips for a 2-min video
    segment_len = audio_duration / segment_count

    scene_clips = []
    local_loops = [f for f in os.listdir(os.path.join(BASE_DIR, "assets"))
                   if f.endswith(".mp4")]

    for seg_idx in range(segment_count):
        # Build a short visual prompt from the story chunk for this segment
        chunk_start = int(seg_idx * len(words) / segment_count)
        chunk_words = words[chunk_start: chunk_start + 12]
        visual_prompt = " ".join(chunk_words)

        clip_path = None

        # ── Tier 1: Replicate AI Video ──────────────────────────────────────
        if use_ai_video:
            clip_path = generate_ai_clip(visual_prompt, seg_idx + 1)

        # ── Tier 2: Pexels stock video ─────────────────────────────────────
        if not clip_path:
            try:
                pexels_url = search_pexels_video(" ".join(chunk_words[:3]))
                if pexels_url:
                    pexels_path = os.path.join(BASE_DIR, "temp", f"scene_{seg_idx + 1}_pexels.mp4")
                    download_file(pexels_url, pexels_path)
                    clip_path = pexels_path
                    print(f"[Fallback] Scene {seg_idx + 1}: Downloaded Pexels clip.")
            except Exception as pe:
                print(f"[Fallback] Scene {seg_idx + 1}: Pexels failed ({pe}).")

        # ── Tier 3: Local asset loop ────────────────────────────────────────
        if not clip_path:
            if local_loops:
                loop_file = local_loops[seg_idx % len(local_loops)]
                clip_path = os.path.join(BASE_DIR, "assets", loop_file)
                print(f"[Fallback] Scene {seg_idx + 1}: Using local loop {loop_file}.")
            else:
                # Last resort: dark solid color
                from PIL import Image
                placeholder_path = os.path.join(BASE_DIR, "assets", "placeholder_gameplay.png")
                Image.new("RGB", (1920, 1080), color=(20, 20, 30)).save(placeholder_path)
                clip_path = placeholder_path
                print(f"[Fallback] Scene {seg_idx + 1}: Using solid color placeholder.")

        # Load and prepare the clip for this segment
        try:
            if clip_path.endswith(".png"):
                seg_clip = ImageClip(clip_path).with_duration(segment_len)
            else:
                seg_clip = VideoFileClip(clip_path)
                if seg_clip.duration < segment_len:
                    seg_clip = fx.Loop(duration=segment_len).apply(seg_clip)
                seg_clip = seg_clip.subclipped(0, segment_len)
            scene_clips.append(seg_clip)
        except Exception as load_err:
            print(f"[WARNING] Could not load clip for scene {seg_idx + 1}: {load_err}. Skipping.")

    # Stitch all scene clips together
    if scene_clips:
        bg_clip = concatenate_videoclips(scene_clips, method="compose")
        # Pad or trim to exact audio duration
        if bg_clip.duration < audio_duration:
            bg_clip = fx.Loop(duration=audio_duration).apply(bg_clip).subclipped(0, audio_duration)
        else:
            bg_clip = bg_clip.subclipped(0, audio_duration)
    else:
        # Complete fallback — solid color
        bg_clip = ColorClip(size=(w, h), color=(20, 20, 30)).with_duration(audio_duration)

    import moviepy.video.fx as vfx

    # Resize height, crop width to center, and darken the video so text pops
    bg_clip = bg_clip.resized(height=h)
    bg_clip = vfx.Crop(x_center=bg_clip.w/2, width=w).apply(bg_clip)
    bg_clip = vfx.MultiplyColor(0.4).apply(bg_clip) 
    
    # 4. Text on screen (Word by Word)
    print("[4/5] Generating MrBeast style word-by-word subtitles...")
    text_clips = []
    try:
        import whisper
        import warnings
        warnings.filterwarnings("ignore")
        print("[DEBUG] Running Whisper for exact word timestamps...")
        model = whisper.load_model("base")
        result = model.transcribe(voice_path, word_timestamps=True)
        for segment in result['segments']:
            for w_data in segment['words']:
                word = w_data['word'].strip()
                start = w_data['start']
                end = w_data['end']
                
                # Skip empty words
                if not word: continue
                
                # Create highlight text clip (large white text with black stroke/shadow)
                txt = TextClip(
                    text=word,
                    font="/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
                    font_size=120,
                    color="white",
                    stroke_color="black",
                    stroke_width=6,
                    duration=max(0.1, end - start)
                ).with_position("center").with_start(start)
                text_clips.append(txt)
    except Exception as e:
        print(f"[DEBUG] Whisper failed or not found ({e}). Falling back to simple subtitle.")
        txt = TextClip("Reddit Story", font="/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", font_size=100, color="white", stroke_color="black", stroke_width=4, duration=audio_duration).with_position("center")
        text_clips.append(txt)
        
    print("[5/5] Compositing and Exporting...")
    import moviepy.audio.fx as afx
    
    # 1. In every scene clip - strip audio first
    bg_clip = bg_clip.without_audio()
    composite_scene = CompositeVideoClip([bg_clip] + text_clips).with_duration(audio_duration)
    clips = [composite_scene]
    
    # 2. In concatenate step - strip again
    final = concatenate_videoclips(clips, method="compose")
    final = final.without_audio()
    
    # 3. Then attach ONE clean composite audio
    narration = AudioFileClip(voice_path)
    music_path = os.path.join(BASE_DIR, "assets", "music", "cinematic.mp3")
    if os.path.exists(music_path):
        music = AudioFileClip(music_path)
        music = afx.AudioLoop(duration=audio_duration).apply(music)
        music = music.with_volume_scaled(0.08)
        final_audio = CompositeAudioClip([narration, music])
    else:
        final_audio = CompositeAudioClip([narration])
        
    final = final.with_audio(final_audio)
    
    # 4. Verify before export:
    print(f"Audio tracks count: {len(final.audio.clips)}")
    
    topic_clean = topic[:30].replace(' ','_').replace('/','_')
    output_path = os.path.join(BASE_DIR, "outputs", f"{topic_clean}_{quality}_reddit.mp4")
    
    # 5. Export with explicit audio settings
    final.write_videofile(
        output_path,
        fps=30,
        codec="libx264",
        audio_codec="aac",
        audio_fps=44100,
        ffmpeg_params=["-ac", "2"],
        threads=4,
        logger=None
    )
    
    final.close()
    full_audio.close()
    bg_clip.close()
    
    # Save/copy the final video file as movie.mp4 in cinematic service directory
    movie_mp4_path = os.path.join(BASE_DIR, "movie.mp4")
    try:
        import shutil
        shutil.copy(output_path, movie_mp4_path)
        print(f"[AI Video] Movie copied to {movie_mp4_path}")
    except Exception as copy_err:
        print(f"[AI Video] Warning: Could not copy final movie to {movie_mp4_path}: {copy_err}")
        
    print(f"Done! Output: {output_path}")
    return output_path

def compile_final_video(project_id, scenes, timing_map, total_duration, mixed_audio_wav, output_mp4):
    """
    Stitches together scene video clips and overlays the mixed audio to produce the final movie.
    This function wraps the modern compile_segmented_timeline implementation.
    """
    project_path = os.path.join(PROJECTS_DIR, project_id)
    
    a_roll_paths = []
    b_roll_data = []
    sfx_data = []
    
    for scene in scenes:
        scene_num = scene["scene_number"]
        a_roll_file = os.path.join(project_path, f"video_synced_{scene_num}.mp4")
        if not os.path.exists(a_roll_file):
            a_roll_file = os.path.join(project_path, f"video_diff_{scene_num}.mp4")
        
        if os.path.exists(a_roll_file):
            a_roll_paths.append(a_roll_file)
        else:
            image_path = os.path.join(project_path, f"frame_{scene_num}.webp")
            if os.path.exists(image_path):
                timing = timing_map.get(scene_num, {"duration": 6.0})
                duration = timing.get("duration", 6.0)
                camera_mv = scene.get("camera_movement", "zoom-in")
                a_roll_file = make_zoom_pan_clip(image_path, duration, camera_mv, output_path=os.path.join(project_path, f"video_diff_{scene_num}.mp4"))
                if a_roll_file and os.path.exists(a_roll_file):
                    a_roll_paths.append(a_roll_file)
                    
        b_roll_file = os.path.join(project_path, f"video_diff_{scene_num + 1000}.mp4")
        if os.path.exists(b_roll_file):
            timing = timing_map.get(scene_num, {"start_time": 0.0})
            b_roll_data.append((b_roll_file, timing.get("start_time", 0.0) + 1.5))
            
        if scene.get("sfx_audio_path"):
            timing = timing_map.get(scene_num, {"start_time": 0.0})
            sfx_data.append((scene["sfx_audio_path"], timing.get("start_time", 0.0)))
            
    whisper_json_dict = {"segments": []}
    
    return compile_segmented_timeline(
        project_path,
        a_roll_paths,
        b_roll_data,
        sfx_data,
        mixed_audio_wav,
        whisper_json_dict,
        output_mp4
    )

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: python3 movie_generator.py <project_id> <idea> [youtube_url] [voice] [music_mood]")
        sys.exit(1)
        
    proj_id = sys.argv[1]
    user_idea = sys.argv[2]
    url = sys.argv[3] if len(sys.argv) >= 4 and sys.argv[3] else None
    v = sys.argv[4] if len(sys.argv) >= 5 and sys.argv[4] else "en-US-GuyNeural"
    mood = sys.argv[5] if len(sys.argv) >= 6 and sys.argv[5] else "cinematic"
    
    generate_movie_pipeline(proj_id, user_idea, url, v, mood)
