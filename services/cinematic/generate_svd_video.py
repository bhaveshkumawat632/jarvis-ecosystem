import os
import shutil
from gradio_client import Client, handle_file

hf_token = "HF_TOKEN_HERE"
image_path = "/home/junglee01/.gemini/antigravity-cli/brain/8743d446-fa75-42ae-851f-174312e37855/astronaut_gem_explosion_1781644334272.jpg"

OUTPUT_DIR = "/home/junglee01/jarvis_universal/outputs"
os.makedirs(OUTPUT_DIR, exist_ok=True)
dest_mp4 = os.path.join(OUTPUT_DIR, "SVD_Astronaut_Explosion.mp4")

print("Contacting StabilityAI/Stable-Video-Diffusion on HF Space...")
try:
    client = Client("stabilityai/stable-video-diffusion", token=hf_token)
    print("Uploading image and rendering video via SVD... This may take a minute.")
    
    result = client.predict(
        image=handle_file(image_path),
        seed=42,
        randomize_seed=True,
        motion_bucket_id=127,
        fps_id=12,
        api_name="/video"
    )
    
    video_dict = result[0]
    video_path = video_dict.get("video")
    
    if video_path and os.path.exists(video_path):
        shutil.copy(video_path, dest_mp4)
        print(f"DONE! Video saved to {dest_mp4}")
    else:
        print("Failed to get a valid video path from HF Space.")
        print("Result:", result)
except Exception as e:
    print(f"Error calling HF Space: {e}")
