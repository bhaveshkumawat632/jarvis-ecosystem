import os
import sys

sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from memory.ffmpeg_editor import FFmpegAssemblyEngine

def test_real_editor_pipeline():
    print("=======================================")
    print("[*] Testing Real FFmpeg Assembly Engine")
    print("=======================================")

    editor = FFmpegAssemblyEngine()
    project_id = "real_project_456"

    # Define paths to the dummy media created earlier
    base_dir = os.path.dirname(os.path.abspath(__file__))
    vid1 = os.path.join(base_dir, 'test_media', 'scene_0.mp4')
    vid2 = os.path.join(base_dir, 'test_media', 'scene_1.mp4')
    aud1 = os.path.join(base_dir, 'test_media', 'dialogue_0.wav')
    bgm = os.path.join(base_dir, 'test_media', 'bgm.wav')

    print("\n[+] 1. Validating Actual Media Assets...")
    try:
        editor.validate_assets([vid1, vid2], [aud1, bgm])
        print("    -> All assets confirmed on disk.")
    except FileNotFoundError as e:
        print(f"    -> Validation failed: {e}")
        return

    print("\n[+] 2. Initializing Render Job...")
    job_id = editor.start_render_job(project_id)
    
    print("\n[+] 3. Building Timeline...")
    chunk_data = editor.build_timeline(project_id, [vid1, vid2], [aud1], bgm)
    
    print("\n[+] 4. Rendering Chunks via Real FFmpeg Subprocess...")
    rendered_chunks = []
    for chunk_name, data in chunk_data.items():
        out_file = editor.render_chunk(job_id, chunk_name, data)
        if out_file:
            print(f"    -> Rendered: {out_file}")
            rendered_chunks.append(out_file)
        else:
            print(f"    -> Chunk render failed.")

    print("\n[+] 5. Lossless Concatenation...")
    if rendered_chunks:
        final_url = editor.concatenate_chunks(job_id, rendered_chunks)
        print(f"    -> Final Output: {final_url}")
        
        # Verify it actually exists
        if os.path.exists(final_url):
            print("    -> SUCCESS: The final .mp4 file physically exists on disk!")
            size = os.path.getsize(final_url) / (1024*1024)
            print(f"    -> File Size: {size:.2f} MB")
        else:
            print("    -> FAILURE: Output file not found.")

if __name__ == "__main__":
    test_real_editor_pipeline()
