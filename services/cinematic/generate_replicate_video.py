import os
import replicate
import requests

os.environ["REPLICATE_API_TOKEN"] = "REPLICATE_API_KEY_HERE"

prompt = "A highly detailed 3D animated cinematic shot of a tiny astronaut in a detailed white spacesuit, standing on the surface of a purple alien planet. The background features a purple sky, floating cosmic dust, and strange rock formations. The astronaut is looking down at a large, glowing orange gem that is resting on the frozen ground. The camera performs a slow tilt-down to reveal the gem, followed by a gentle pan-right showing the surreal landscape. Soft, cinematic volumetric lighting illuminates the scene, creating a sense of awe and discovery."

print("Calling Replicate API (minimax/video-01)... This will take a few minutes.")

try:
    output = replicate.run(
        "minimax/video-01",
        input={
            "prompt": prompt,
            "prompt_optimizer": True
        }
    )
    
    video_url = output
    print(f"Video generated successfully! URL: {video_url}")
    
    # Download the video
    print("Downloading video to outputs/Astronaut_Minimax.mp4...")
    response = requests.get(video_url)
    output_path = "/home/junglee01/jarvis_universal/outputs/Astronaut_Minimax.mp4"
    with open(output_path, "wb") as f:
        f.write(response.content)
    print(f"DONE! Saved to {output_path}")

except Exception as e:
    print(f"Error calling Replicate: {e}")
