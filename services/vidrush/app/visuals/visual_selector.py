import os
import requests
from configs.settings import ASSETS_DIR
from app.agents.emotion_agent import EmotionAgent

class VisualSelector:
    def __init__(self):
        self.emotion_agent = EmotionAgent()
        
    def download_file(self, url, dest_path):
        os.makedirs(os.path.dirname(dest_path), exist_ok=True)
        r = requests.get(url, stream=True, timeout=15)
        r.raise_for_status()
        with open(dest_path, 'wb') as f:
            for chunk in r.iter_content(chunk_size=8192):
                if chunk: f.write(chunk)
        return dest_path

    def generate_video_replicate(self, prompt: str):
        try:
            import replicate
            print(f"Generating true AI video via Replicate for prompt: {prompt}")
            # Use a fast text-to-video model (e.g. zeroscope or similar standard models available)
            output = replicate.run(
                "lucataco/hotshot-xl:ce8eaec152d0b5e1e127bf3ce2370ae9a9f2ceee8b4fdf186fb5c3d4af9dc835",
                input={
                    "prompt": prompt,
                    "negative_prompt": "blurry, low quality, distorted, bad anatomy",
                    "width": 672,
                    "height": 384,
                    "video_length": 8
                }
            )
            # output is typically a URL string to an mp4 file
            if isinstance(output, str) and output.startswith("http"):
                return output
            elif isinstance(output, list) and len(output) > 0:
                return output[0]
            elif hasattr(output, "url"): # file object
                return output.url
        except Exception as e:
            print(f"Replicate generation failed: {e}")
            return None
        return None

    def select_background(self, topic: str, script_text: str):
        analysis = self.emotion_agent.analyze(script_text)
        emotion = analysis.get("emotion", "neutral")
        
        import hashlib
        safe_hash = hashlib.md5(topic.encode()).hexdigest()[:8]
        out_path = os.path.join(ASSETS_DIR, f"dynamic_bg_{safe_hash}.mp4")
        
        if not os.path.exists(out_path):
            # Attempt true AI video generation based on the topic
            gen_url = self.generate_video_replicate(topic)
            if not gen_url:
                # Fallback to emotion query if specific topic fails
                gen_url = self.generate_video_replicate(f"{emotion} cinematic abstract background")
            
            if gen_url:
                print(f"Downloading generated Replicate video for topic '{topic}'...")
                self.download_file(gen_url, out_path)
            else:
                # Local procedural generator – guaranteed to work without external services
                from .procedural_generator import generate_particles_video
                print("Replicate unavailable – generating procedural particle video.")
                try:
                    proc_path = generate_particles_video(duration=5, fps=24, size=(1080, 1920), topic=topic, emotion=emotion)
                    # Move the generated file to the expected asset location
                    os.replace(proc_path, out_path)
                    print(f"Procedural video saved to {out_path}")
                except Exception as e:
                    print(f"Procedural generation failed: {e}")
                    # Fallback to a 1‑second black video via ffmpeg (still better than nothing)
                    import subprocess
                    cmd = [
                        "ffmpeg", "-y",
                        "-f", "lavfi",
                        "-i", "color=c=black:s=1080x1920:d=1",
                        "-c:v", "libx264",
                        out_path,
                    ]
                    subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                    print(f"Fallback black video created at {out_path}")
        
        return out_path, analysis

if __name__ == "__main__":
    selector = VisualSelector()
    bg, info = selector.select_background("Dark abandoned city", "This is very scary")
    print(f"Selected: {bg}, Info: {info}")
