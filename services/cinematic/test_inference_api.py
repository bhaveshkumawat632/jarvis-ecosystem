import requests
import io
from PIL import Image

hf_token = "HF_TOKEN_HERE"
model_id = "black-forest-labs/FLUX.1-schnell"
# Or stabilityai/stable-diffusion-3.5-large

print(f"--- Testing HF Serverless Inference API: {model_id} ---")
API_URL = f"https://api-inference.huggingface.co/models/{model_id}"
headers = {"Authorization": f"Bearer {hf_token}"}

payload = {
    "inputs": "A beautiful digital garden, 3D render, cinematic, 1024x576",
}

try:
    response = requests.post(API_URL, headers=headers, json=payload, timeout=30)
    print("Status code:", response.status_code)
    if response.status_code == 200:
        image = Image.open(io.BytesIO(response.content))
        print("Success! Image size:", image.size)
        image.save("test_out.webp")
        print("Saved test_out.webp")
    else:
        print("Error Response:", response.text)
except Exception as e:
    print("Failed:", e)
