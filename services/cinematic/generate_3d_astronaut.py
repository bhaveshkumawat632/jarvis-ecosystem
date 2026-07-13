import os
import shutil
from gradio_client import Client, handle_file

hf_token = "HF_TOKEN_HERE"
image_path = "/home/junglee01/.gemini/antigravity-cli/brain/8743d446-fa75-42ae-851f-174312e37855/astronaut_purple_planet_1781642216142.jpg"

OUTPUT_DIR = "/home/junglee01/jarvis_universal/outputs"
os.makedirs(OUTPUT_DIR, exist_ok=True)
dest_glb = os.path.join(OUTPUT_DIR, "Astronaut_3D_Model.glb")
dest_obj = os.path.join(OUTPUT_DIR, "Astronaut_3D_Model.obj")

print("Contacting StabilityAI/TripoSR for 3D generation...")
try:
    client = Client("stabilityai/TripoSR", token=hf_token)
    
    print("Step 1: Preprocessing image (removing background)...")
    processed_image = client.predict(
        handle_file(image_path),
        True,
        0.85,
        api_name="/preprocess"
    )
    
    print("Step 2: Generating 3D Model (GLB & OBJ)...")
    obj_path, glb_path = client.predict(
        handle_file(processed_image),
        256,
        api_name="/generate"
    )
    
    if glb_path and os.path.exists(glb_path):
        shutil.copy(glb_path, dest_glb)
        print(f"DONE! GLB saved to {dest_glb}")
    
    if obj_path and os.path.exists(obj_path):
        shutil.copy(obj_path, dest_obj)
        print(f"DONE! OBJ saved to {dest_obj}")
        
except Exception as e:
    print(f"Error calling HF Space: {e}")
