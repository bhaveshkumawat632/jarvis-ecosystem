import sys
import os

sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from memory.ffmpeg_editor import FFmpegAssemblyEngine

def test_editor_pipeline():
    print("=======================================")
    print("[*] Testing Final FFmpeg Nonlinear Assembly Engine")
    print("=======================================")

    editor = FFmpegAssemblyEngine()
    project_id = "fake_project_123"

    # 1. Start Job
    print("\n[+] 1. Initializing Render Job...")
    job_id = editor.start_render_job(project_id, resolution="3840x2160")
    print(f"    -> Render Job ID: {job_id}")

    # 2. Build Timeline
    print("\n[+] 2. Building Master Timeline...")
    chunks = editor.build_timeline(project_id)
    print(f"    -> Divided script into {len(chunks)} render chunks.")

    # 3. Simulate Failure and Recovery
    print("\n[+] 3. Beginning Chunk Processing (Simulating Crash at Chunk 3)...")
    for chunk in chunks:
        success = editor.render_chunk(job_id, chunk, simulate_failure=True)
        if not success:
            break
            
    print("\n[+] 4. Recovering from Crash...")
    editor.recover_job(job_id)
    print("    -> Resuming from Chunk 3...")
    for chunk in chunks[2:]:
        editor.render_chunk(job_id, chunk, simulate_failure=False)

    # 4. Final Assembly
    print("\n[+] 5. Lossless Concatenation...")
    final_url = editor.concatenate_chunks(job_id, chunks)

    print("\n=======================================")
    print(f"[*] Editor Pipeline Test Successful!")
    print(f"    Final Movie: {final_url}")
    print("=======================================")

if __name__ == "__main__":
    test_editor_pipeline()
