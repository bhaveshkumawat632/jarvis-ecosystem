from movie_generator import generate_movie_pipeline
import os

os.environ["GROQ_API_KEY"] = "GROQ_API_KEY_HERE"
os.environ["PEXELS_API_KEY"] = "PEXELS_API_KEY_HERE"
os.environ["OPENAI_API_KEY"] = "7d34f448-046e-4c4a-98ec-5638270c1d55"
os.environ["REPLICATE_API_TOKEN"] = "REPLICATE_API_KEY_HERE"
hf_token = "HF_TOKEN_HERE"

idea = """
The AI Revolution (2026-2030): How to Survive & Multi-Million Dollar Skills.
A cinematic documentary about the AI revolution. 
1. The Hook & The Problem: AI robots, coding screens, matrix falling code, breaking news clips of job layoffs.
2. The Current Reality Check: AI writing code and videos. High-tech futuristic data centers.
3. Core Blueprint: High-Income Skills.
4. Step-by-Step Action Plan.
5. Conclusion & The Golden Advice.
"""

print("Starting Jarvis Universal Movie Generator Pipeline...")
final_video = generate_movie_pipeline(
    project_id="AI_Revolution_Movie",
    idea=idea,
    voice="en-US-ChristopherNeural",
    music_mood="cinematic",
    hf_token=hf_token
)

print(f"PIPELINE COMPLETE! Final video is at: {final_video}")
