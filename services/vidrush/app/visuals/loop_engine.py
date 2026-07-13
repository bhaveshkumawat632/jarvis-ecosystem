import os
import subprocess

class LoopEngine:
    def process(self, input_video, duration, output_path):
        """
        Uses FFmpeg to crop to 9:16 (1080x1920), loop to match duration.
        Kept lightweight for fast rendering.
        """
        # Cap duration to avoid extremely long renders
        duration = min(float(duration), 120)
        
        print(f"[LoopEngine] Looping {input_video} to {duration:.1f}s → {output_path}")
        
        # Simple scale + crop, no heavy blur/color transforms
        filter_str = "scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920"
        
        cmd = [
            "ffmpeg", "-y",
            "-stream_loop", "-1",
            "-i", input_video,
            "-t", str(duration),
            "-vf", filter_str,
            "-c:v", "libx264",
            "-preset", "ultrafast",
            "-an",
            output_path
        ]
        
        print(f"[LoopEngine] Running: {' '.join(cmd)}")
        subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE)
        print(f"[LoopEngine] Done → {output_path}")
        return output_path

