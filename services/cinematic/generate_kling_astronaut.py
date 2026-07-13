import os
import time
import jwt
import requests
import json

KLING_ACCESS_KEY = "KLING_ACCESS_KEY_HERE"
KLING_SECRET_KEY = "KLING_SECRET_KEY_HERE"

def generate_kling_token():
    headers = {"alg": "HS256", "typ": "JWT"}
    payload = {
        "iss": KLING_ACCESS_KEY,
        "exp": int(time.time()) + 1800,
        "nbf": int(time.time()) - 5
    }
    return jwt.encode(payload, KLING_SECRET_KEY, algorithm="HS256", headers=headers)

token = generate_kling_token()
print("Kling Token Generated.")

url = "https://api.klingai.com/v1/videos/text2video"
headers = {
    "Authorization": f"Bearer {token}",
    "Content-Type": "application/json"
}
payload = {
    "model": "kling-v1",
    "prompt": "A highly detailed 3D animated cinematic shot of a tiny astronaut in a detailed white spacesuit, standing on the surface of a purple alien planet. The background features a purple sky, floating cosmic dust, and strange rock formations. The astronaut is looking down at a large, glowing orange gem that is resting on the frozen ground. The camera performs a slow tilt-down to reveal the gem, followed by a gentle pan-right showing the surreal landscape. Soft, cinematic volumetric lighting illuminates the scene, creating a sense of awe and discovery.",
    "duration": 5
}

print("Submitting prompt to Kling AI...")
response = requests.post(url, json=payload, headers=headers)
data = response.json()
print("Submit Response:", response.status_code, data)

if response.status_code == 200 and data.get("code") == 0:
    task_id = data["data"]["task_id"]
    print(f"Task successfully submitted! Task ID: {task_id}")
    
    # Polling for completion
    poll_url = f"https://api.klingai.com/v1/videos/text2video/{task_id}"
    while True:
        print("Polling status...")
        poll_res = requests.get(poll_url, headers=headers)
        poll_data = poll_res.json()
        status = poll_data["data"]["task_status"]
        if status == "succeed":
            video_url = poll_data["data"]["task_result"]["videos"][0]["url"]
            print(f"Video generation complete! URL: {video_url}")
            break
        elif status == "failed":
            print("Video generation failed!", poll_data)
            exit(1)
        else:
            time.sleep(5)
            
    # Download video
    print("Downloading video to outputs/Kling_Astronaut.mp4...")
    os.makedirs("/home/junglee01/jarvis_universal/outputs", exist_ok=True)
    video_res = requests.get(video_url)
    with open("/home/junglee01/jarvis_universal/outputs/Kling_Astronaut.mp4", "wb") as f:
        f.write(video_res.content)
    print("DONE! File saved.")
else:
    print("Failed to submit task.", data)
