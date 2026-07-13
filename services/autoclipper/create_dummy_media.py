import subprocess
import os

MEDIA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'test_media')

def create_media():
    os.makedirs(MEDIA_DIR, exist_ok=True)
    
    # Create 3 small video files
    for i, color in enumerate(['red', 'green', 'blue']):
        vid_path = os.path.join(MEDIA_DIR, f'scene_{i}.mp4')
        if not os.path.exists(vid_path):
            subprocess.run([
                'ffmpeg', '-y', '-f', 'lavfi', '-i', f'color=c={color}:s=640x360:d=2', 
                '-c:v', 'libx264', '-t', '2', vid_path
            ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            
    # Create audio dialogue
    audio_path = os.path.join(MEDIA_DIR, 'dialogue_0.wav')
    if not os.path.exists(audio_path):
        subprocess.run([
            'ffmpeg', '-y', '-f', 'lavfi', '-i', 'sine=frequency=440:duration=2', 
            '-c:a', 'pcm_s16le', audio_path
        ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

    # Create bgm
    bgm_path = os.path.join(MEDIA_DIR, 'bgm.wav')
    if not os.path.exists(bgm_path):
        subprocess.run([
            'ffmpeg', '-y', '-f', 'lavfi', '-i', 'sine=frequency=220:duration=6', 
            '-c:a', 'pcm_s16le', bgm_path
        ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

    print(f"[*] Created real dummy media files in {MEDIA_DIR}")

if __name__ == '__main__':
    create_media()
