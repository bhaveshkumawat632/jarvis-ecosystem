import sys
from unittest.mock import MagicMock

# Mock heavy modules before importing movie_generator
sys.modules['TTS'] = MagicMock()
sys.modules['TTS.api'] = MagicMock()
sys.modules['diffusers'] = MagicMock()
sys.modules['torch'] = MagicMock()
sys.modules['scipy.io.wavfile'] = MagicMock()
sys.modules['scipy.io'] = MagicMock()
sys.modules['scipy'] = MagicMock()

from movie_generator import generate_movie_pipeline, LocalAudioFoundry
import movie_generator
import os

os.environ["GROQ_API_KEY"] = "GROQ_API_KEY_HERE"
os.environ["PEXELS_API_KEY"] = "PEXELS_API_KEY_HERE"
os.environ["OPENAI_API_KEY"] = "7d34f448-046e-4c4a-98ec-5638270c1d55"
os.environ["REPLICATE_API_TOKEN"] = "REPLICATE_API_KEY_HERE"
hf_token = "HF_TOKEN_HERE"

idea = """
A 3 scene micro-test.
1. The hero wakes up in a futuristic city.
2. The hero drinks coffee while looking at a hologram.
3. The hero steps outside and gets into a flying car.
"""

# Mock heavy APIs
movie_generator.LocalAudioFoundry.generate_dialogue = lambda self, text, spk, dest, **kwargs: open(dest, "wb").write(b"audio data")
movie_generator.LocalAudioFoundry.generate_foley_ambient = lambda self, prompt, dest, **kwargs: open(dest, "wb").write(b"audio data")
movie_generator.LocalAudioFoundry.unload_models = lambda self: None
movie_generator.generate_frames = lambda *args, **kwargs: None
movie_generator.build_voiceover_track = lambda a,b,c: ("mixed.wav", [{"start_time": 0.0, "duration": 6.0}, {"start_time": 6.0, "duration": 6.0}, {"start_time": 12.0, "duration": 6.0}], 18.0)
movie_generator.generate_script_old = lambda *args, **kwargs: {"scenes": [
    {"scene_number": 1, "narration": "test", "image_prompt": "test 1"},
    {"scene_number": 2, "narration": "test", "image_prompt": "test 2"},
    {"scene_number": 3, "narration": "test", "image_prompt": "test 3"}
], "title": "test", "distribution_metadata": {}}
movie_generator.generate_storyboard = lambda *args, **kwargs: {"scenes": [
    {"scene_number": 1, "narration": "test", "image_prompt": "test 1"},
    {"scene_number": 2, "narration": "test", "image_prompt": "test 2"},
    {"scene_number": 3, "narration": "test", "image_prompt": "test 3"}
]}
movie_generator.extract_qa_frames = lambda *args, **kwargs: ["base64_string"]
movie_generator.qa_video_asset = lambda *args, **kwargs: (True, "Looks good")
movie_generator.compile_segmented_timeline = lambda *args, **kwargs: "final.mp4"

original_generate = movie_generator.generate_local_video_comfyui
call_count = 0

def mock_generate(prompt, output_path, reference_image_path=None):
    global call_count
    call_count += 1
    if call_count == 2 and not os.path.exists("crash.flag"):
        print(">> SIMULATING CTRL+C MIDWAY THROUGH SCENE 2 <<")
        open("crash.flag", "w").close()
        raise KeyboardInterrupt("Simulated Ctrl+C")
    print(f"Mock rendering {output_path}")
    open(output_path, "wb").write(b"video data")

movie_generator.generate_local_video_comfyui = mock_generate

print("--- RUN 1: STARTING PIPELINE ---")
try:
    generate_movie_pipeline(project_id="sandbox_trial", idea=idea)
except KeyboardInterrupt:
    print("Pipeline interrupted!")

print("\n--- RUN 2: RESTARTING PIPELINE ---")
generate_movie_pipeline(project_id="sandbox_trial", idea=idea)
print("Pipeline finished successfully.")
