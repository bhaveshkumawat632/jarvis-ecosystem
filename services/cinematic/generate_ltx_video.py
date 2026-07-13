import os
import shutil
from gradio_client import Client, handle_file

hf_token = "HF_TOKEN_HERE"
prompt = "Fast camera pan over hands typing rapidly on a mechanical keyboard. Lines of matrix code reflect dynamically on the glowing monitor. Cyberpunk aesthetic, neon blue and orange lighting, dark atmosphere."
image_path = "/home/junglee01/.gemini/antigravity-cli/brain/8743d446-fa75-42ae-851f-174312e37855/cyberpunk_developer_workspace_1781644962744.jpg"

OUTPUT_DIR = "/home/junglee01/jarvis_universal/outputs"
os.makedirs(OUTPUT_DIR, exist_ok=True)
dest_mp4 = os.path.join(OUTPUT_DIR, "Cyberpunk_Developer_LTX.mp4")

print("Contacting Lightricks/LTX-2-3 for Image-to-Video...")
try:
    client = Client("Lightricks/LTX-2-3", token=hf_token)
    print("Uploading image and rendering video... This may take a minute.")
    
    result = client.predict(
        input_image=handle_file(image_path),
        prompt=prompt,
        duration=3.0,
        enhance_prompt=False,
        seed=42,
        randomize_seed=True,
        height=512,
        width=768,
        api_name="/generate_video"
    )
    
    video_path = result[0]
    if video_path and os.path.exists(video_path):
        shutil.copy(video_path, dest_mp4)
        print(f"DONE! Video saved to {dest_mp4}")
    else:
        print("Failed to get a valid video path from HF Space.")
        print("Result:", result)
except Exception as e:
    print(f"Error calling HF Space: {e}")
