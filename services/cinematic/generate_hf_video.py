import os
import shutil
from gradio_client import Client

hf_token = "HF_TOKEN_HERE"
prompt = "A highly detailed 3D animated cinematic shot of a tiny astronaut in a detailed white spacesuit, standing on the surface of a purple alien planet. The background features a purple sky, floating cosmic dust, and strange rock formations. The astronaut is looking down at a large, glowing orange gem that is resting on the frozen ground. The camera performs a slow tilt-down to reveal the gem, followed by a gentle pan-right showing the surreal landscape. Soft, cinematic volumetric lighting illuminates the scene, creating a sense of awe and discovery."

OUTPUT_DIR = "/home/junglee01/jarvis_universal/outputs"
os.makedirs(OUTPUT_DIR, exist_ok=True)
dest_mp4 = os.path.join(OUTPUT_DIR, "HF_Zeroscope_Astronaut.mp4")

print("Contacting HuggingFace Space 'hysts/zeroscope-v2'...")
try:
    client = Client("hysts/zeroscope-v2", token=hf_token)
    print("Sending text-to-video request...")
    result = client.predict(
        prompt=prompt,
        seed=42,
        num_frames=24,
        num_inference_steps=20,
        api_name="/run"
    )
    
    if result and os.path.exists(result):
        shutil.copy(result, dest_mp4)
        print(f"DONE! Video saved to {dest_mp4}")
    else:
        print("Failed to get a valid video path from HF Space.")
        print("Result:", result)
except Exception as e:
    print(f"Error calling HF Space: {e}")
