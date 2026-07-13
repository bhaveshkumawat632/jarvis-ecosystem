import os
import shutil
import pytest
from moviepy import ColorClip, AudioArrayClip
import numpy as np
from movie_generator import compile_final_video

@pytest.fixture
def temp_project_dir(tmp_path):
    project_id = "test_project_123"
    project_dir = tmp_path / project_id
    project_dir.mkdir()
    
    # We need to monkeypatch PROJECTS_DIR in movie_generator
    import movie_generator
    movie_generator.PROJECTS_DIR = str(tmp_path)
    
    yield project_id, str(project_dir)

def test_compile_final_video_integration(temp_project_dir):
    project_id, project_path = temp_project_dir
    
    # 1. Create a dummy mixed_audio.wav (1 second of silence)
    fps = 44100
    duration = 1.0
    t = np.linspace(0, duration, int(fps * duration))
    # Create stereo silence
    audio_data = np.zeros((len(t), 2))
    audio_clip = AudioArrayClip(audio_data, fps=fps)
    dummy_audio_path = os.path.join(project_path, "mixed_audio.wav")
    audio_clip.write_audiofile(dummy_audio_path, logger=None)
    
    # 2. Create a dummy generated frame for the scene fallback
    scene_num = 0
    dummy_frame_path = os.path.join(project_path, f"frame_{scene_num}.webp")
    # Instead of an actual image, let's create a solid color dummy MP4 to simulate the fallback behavior directly
    # Wait, the code looks for diff_file, render_3d_file, or img_file.
    # Let's provide a dummy diff_file so it doesn't need to do zoom_pan (which requires real images)
    dummy_diff_path = os.path.join(project_path, f"video_diff_{scene_num}.mp4")
    color_clip = ColorClip(size=(640, 360), color=(255, 0, 0), duration=1.0)
    color_clip.write_videofile(dummy_diff_path, fps=24, logger=None)
    
    scenes = [
        {"scene_number": scene_num, "camera_movement": "zoom-in"}
    ]
    timing_map = {
        0: {"duration": 1.0}
    }
    
    output_mp4 = os.path.join(project_path, "final_output.mp4")
    
    # Run the integration method
    try:
        compile_final_video(
            project_id=project_id,
            scenes=scenes,
            timing_map=timing_map,
            total_duration=1.0,
            mixed_audio_wav=dummy_audio_path,
            output_mp4=output_mp4
        )
        success = True
    except Exception as e:
        print(f"Integration failed: {e}")
        success = False
        
    assert success == True
    assert os.path.exists(output_mp4), "Final output video was not created"
    
    # Check if we can read the generated file
    assert os.path.getsize(output_mp4) > 1000, "Output video is suspiciously small"
