import os
import json
import re
import cv2
import subprocess
import yt_dlp
from celery import Celery
from faster_whisper import WhisperModel
from openai import OpenAI

import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from jarvis_core_lib.config import PipelineConfig

celery_app = Celery('autoclipper.tasks', broker='redis://localhost:6379/0')

print("[*] Loading CPU-Optimized Whisper Model (base.en) into RAM...")
whisper_model = WhisperModel("base.en", device="cpu", compute_type="int8")

nim_client = OpenAI(
    base_url="https://integrate.api.nvidia.com/v1",
    api_key=PipelineConfig.NVIDIA_API_KEY
)
NEMOTRON_MODEL = "nvidia/nemotron-3-super-120b-a12b"
face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')

def seconds_to_srt_time(secs):
    """Helper to convert raw seconds into standard SRT timestamp formatting."""
    hours = int(secs // 3600)
    minutes = int((secs % 3600) // 60)
    seconds = int(secs % 60)
    milliseconds = int((secs - int(secs)) * 1000)
    return f"{hours:02d}:{minutes:02d}:{seconds:02d},{milliseconds:03d}"

@celery_app.task(bind=True, name="autoclipper.process_viral_clip", max_retries=3)
def process_viral_clip(self, project_id, youtube_url):
    print(f"[*] [Worker] Initiating Auto-Clipper for {project_id}")
    project_dir = f"/home/junglee01/jarvis_universal/projects/{project_id}"
    os.makedirs(project_dir, exist_ok=True)

    source_video_path = os.path.join(project_dir, 'source_video.mp4')
    
    # --- STEP 1: INGESTION (Optimized for H.264 to protect CPU) ---
    if not os.path.exists(source_video_path):
        print(f"[*] Downloading H.264 source video: {youtube_url}")
        ydl_opts = {
            'format': 'bestvideo[vcodec^=avc]+bestaudio[ext=m4a]/best[vcodec^=avc]',
            'outtmpl': source_video_path,
            'quiet': True
        }
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([youtube_url])

    # --- STEP 2: TRANSCRIPTION ---
    transcript_path = os.path.join(project_dir, 'transcript.txt')
    if not os.path.exists(transcript_path):
        print(f"[*] Commencing INT8 CPU Transcription...")
        segments, _ = whisper_model.transcribe(source_video_path, beam_size=5, vad_filter=True)
        
        raw_segments_data = []
        full_text_corpus = ""
        for s in segments:
            raw_segments_data.append({"start": s.start, "end": s.end, "text": s.text.strip()})
            full_text_corpus += f"[{round(s.start, 2)} - {round(s.end, 2)}] {s.text.strip()}\n"
            
        with open(transcript_path, 'w', encoding='utf-8') as f:
            f.write(full_text_corpus)
            
        # Keep structured raw JSON segments for captioning
        with open(os.path.join(project_dir, 'segments.json'), 'w') as f:
            json.dump(raw_segments_data, f, indent=4)

    with open(transcript_path, 'r', encoding='utf-8') as f:
        full_text_corpus = f.read()

    # --- STEP 3: COGNITIVE CURATION (MULTI-CLIP UPGRADE) ---
    plan_path = os.path.join(project_dir, 'viral_plan.json')
    if not os.path.exists(plan_path):
        print("[*] Querying Nemotron-3-Super for TOP 5 viral hooks...")
        system_prompt = """You are a viral content producer. Analyze the transcript. Return ONLY JSON matching this schema: {"clips": [{"start": float, "end": float, "title": "string", "reason": "string"}]} representing the TOP 5 most viral, engaging segments. Each segment MUST be exactly 30 to 60 seconds long. Do not overlap them."""
        
        completion = nim_client.chat.completions.create(
            model=NEMOTRON_MODEL, messages=[{"role": "system", "content": system_prompt}, {"role": "user", "content": full_text_corpus}], temperature=0.2
        )
        
        # Safe extraction
        raw_response = completion.choices[0].message.content
        json_match = re.search(r'\{.*\}', raw_response, re.DOTALL)
        sanitized_json = json_match.group(0) if json_match else raw_response
        clip_data = json.loads(sanitized_json)
        with open(plan_path, 'w', encoding='utf-8') as f:
            json.dump(clip_data, f, indent=4)
            
    with open(plan_path, 'r', encoding='utf-8') as f:
        clip_data = json.load(f)

    # LOOP THROUGH ALL 5 CLIPS
    rendered_clips = []
    for idx, clip in enumerate(clip_data.get('clips', [])):
        start_time = clip['start']
        end_time = clip['end']
        
        # Create a safe filename from the LLM's title
        safe_title = "".join([c for c in clip['title'] if c.isalpha() or c.isdigit() or c==' ']).rstrip().replace(" ", "_")
        print(f"\n=======================================")
        print(f"[*] Processing Clip {idx+1}/{len(clip_data.get('clips', []))}: {safe_title}")
        print(f"=======================================")

        # --- STEP 4: OPENCV FACE TRACKING (PER CLIP) ---
        coord_path = os.path.join(project_dir, f'crop_coordinates_{idx}.json')
        if not os.path.exists(coord_path):
            cap = cv2.VideoCapture(source_video_path)
            fps, width, height = cap.get(cv2.CAP_PROP_FPS), int(cap.get(cv2.CAP_PROP_FRAME_WIDTH)), int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
            target_width = int(height * (9 / 16))
            cap.set(cv2.CAP_PROP_POS_MSEC, start_time * 1000)
            
            frame_skip, frame_count, current_center_x, tracking_data = max(1, int(fps / 3)), 0, width // 2, []
            while cap.isOpened() and cap.get(cv2.CAP_PROP_POS_MSEC) <= (end_time * 1000):
                ret, frame = cap.read()
                if not ret: break
                if frame_count % frame_skip == 0:
                    faces = face_cascade.detectMultiScale(cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY), 1.3, 5, minSize=(60, 60))
                    if len(faces) > 0:
                        faces = sorted(faces, key=lambda x: x[2]*x[3], reverse=True)
                        current_center_x = int((current_center_x * 0.7) + ((faces[0][0] + faces[0][2] // 2) * 0.3))
                    tracking_data.append({"time": round(cap.get(cv2.CAP_PROP_POS_MSEC)/1000, 2), "x": max(0, min(current_center_x - (target_width // 2), width - target_width)), "w": target_width, "h": height})
                frame_count += 1
            cap.release()
            
            # Handle case where clip is so short that tracking data is empty
            if not tracking_data:
                tracking_data.append({"time": 0.0, "x": width // 2 - target_width // 2, "w": target_width, "h": height})
                
            with open(coord_path, 'w') as f: json.dump(tracking_data, f)

        with open(coord_path, 'r') as f: tracking_data = json.load(f)

        # --- STEP 5: FFMPEG SLICING & BURN-IN (PER CLIP) ---
        srt_path = os.path.join(project_dir, f'captions_{idx}.srt')
        with open(os.path.join(project_dir, 'segments.json'), 'r') as f: all_segments = json.load(f)
            
        srt_counter = 1
        with open(srt_path, 'w', encoding='utf-8') as f:
            for seg in all_segments:
                if seg['start'] >= start_time and seg['end'] <= end_time:
                    f.write(f"{srt_counter}\n{seconds_to_srt_time(seg['start'] - start_time)} --> {seconds_to_srt_time(seg['end'] - start_time)}\n{seg['text']}\n\n")
                    srt_counter += 1

        last_x = tracking_data[0]['x']
        filtered_tracking = [tracking_data[0]]
        for entry in tracking_data[1:]:
            if abs(entry['x'] - last_x) > 40:  # Only update if moved by 40+ pixels
                filtered_tracking.append(entry)
                last_x = entry['x']
                
        # Limit to 50 keyframes to prevent FFmpeg Eval crashing
        filtered_tracking = filtered_tracking[:50]
        
        crop_x_expr = f"{filtered_tracking[0]['x']}"
        for entry in reversed(filtered_tracking):
            crop_x_expr = f"if(gte(t,{entry['time'] - start_time}),{entry['x']},{crop_x_expr})"

        output_video_path = os.path.join(project_dir, f'viral_{idx+1}_{safe_title}.mp4')
        
        if os.path.exists(output_video_path) and os.path.getsize(output_video_path) > 0:
            print(f"[*] Clip {idx+1} already exists and is not empty. Skipping transcode.")
            rendered_clips.append(output_video_path)
            continue
        
        ffmpeg_cmd = [
            'ffmpeg', '-y', '-ss', str(start_time), '-to', str(end_time), '-i', source_video_path,
            '-vf', f"crop={tracking_data[0]['w']}:{tracking_data[0]['h']}:'{crop_x_expr}':0,subtitles={srt_path}:force_style='Alignment=2,FontSize=16,PrimaryColour=&H00FFFF,Fontname=Impact',drawtext=text='@Ahgori_':fontcolor=white@0.5:fontsize=42:x=(w-text_w)/2:y=80:shadowcolor=black@0.7:shadowx=2:shadowy=2",
            '-c:v', 'libx264', '-preset', 'ultrafast', '-c:a', 'aac', output_video_path
        ]
        
        print(f"[*] Dispatching transcode pipeline for clip {idx+1}...")
        result = subprocess.run(ffmpeg_cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        if result.returncode != 0:
            print(f"[-] FFmpeg pipeline crashed for clip {idx+1}: {result.stderr}")
        else:
            rendered_clips.append(output_video_path)

    print(f"[+] SUCCESS! Generated {len(rendered_clips)} viral shorts for project: {project_id}")
    return {"status": "COMPLETED", "project_id": project_id, "clips": rendered_clips}
