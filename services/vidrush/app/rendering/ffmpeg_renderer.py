import os
import subprocess

class FFmpegRenderer:
    def __init__(self):
        pass

    def check_cuda(self):
        try:
            res = subprocess.run(["ffmpeg", "-hide_banner", "-hwaccels"], capture_output=True, text=True)
            return "cuda" in res.stdout
        except:
            return False

    def render(self, bg_video, narration_audio, music_audio, ass_subtitles, output_path):
        hwaccel = []
        
        # We need absolute path for ASS filter
        ass_abs = os.path.abspath(ass_subtitles)
        # Fix path for ffmpeg filter (escape colons and slashes if needed on windows, but we are on linux so it's fine)
        ass_filter = f"ass='{ass_abs}'"
        
        if music_audio and os.path.exists(music_audio):
            filter_complex = f"[2:a]volume=0.08[m];[1:a][m]amix=inputs=2:duration=first:dropout_transition=2[a];[0:v]{ass_filter}[v]"
            inputs = ["-i", bg_video, "-i", narration_audio, "-i", music_audio]
        else:
            filter_complex = f"[0:v]{ass_filter}[v];[1:a]volume=1.0[a]"
            inputs = ["-i", bg_video, "-i", narration_audio]

        # Build FFmpeg command with explicit stream mapping. Video comes from filtered output [v];
        # Audio comes from filtered output [a] (narration +/- music). This prevents background audio from overriding TTS.
        cmd = ["ffmpeg", "-y"] + hwaccel + inputs + [
            "-filter_complex", filter_complex,
            "-map", "[v]",   # map processed video with subtitles
            "-map", "[a]",   # map mixed audio (narration + optional music)
            "-c:v", "libx264",
            "-preset", "fast",
            "-c:a", "aac",
            "-b:a", "192k",
            "-ac", "2",
            "-ar", "44100",
            "-shortest",
            output_path
        ]
        
        print("Running FFmpeg render...")
        subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        return output_path

if __name__ == "__main__":
    renderer = FFmpegRenderer()
    print("CUDA available:", renderer.check_cuda())
