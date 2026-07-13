import os
import sys
import time

sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from memory.ffmpeg_editor import FFmpegAssemblyEngine

def run_editor_stress_test():
    editor = FFmpegAssemblyEngine()

    print("Starting Editor Matrix Stress Test (Feature Film Scale Simulation)...")

    start_time = time.time()
    
    # Simulate a massive pipeline of 10 movies rendering simultaneously
    total_chunks_processed = 0
    jobs = []
    
    # 1. Start 10 simultaneous render jobs
    for i in range(10):
        job_id = editor.start_render_job(f"project_{i}")
        chunks = editor.build_timeline(f"project_{i}")
        jobs.append((job_id, chunks))
        
    timeline_calc_time = time.time() - start_time
    
    # 2. Render all chunks (Simulating parallel processing queue overhead)
    render_start = time.time()
    for job_id, chunks in jobs:
        for chunk in chunks:
            editor.render_chunk(job_id, chunk)
            total_chunks_processed += 1
    
    render_time = time.time() - render_start
    
    # 3. Final Concatenation for all jobs
    concat_start = time.time()
    for job_id, chunks in jobs:
        editor.concatenate_chunks(job_id, chunks)
    concat_time = time.time() - concat_start

    total_time = time.time() - start_time

    print("\nEditor Matrix Stress Test Completed.")
    print("Metrics:")
    print(f"Total Movies Rendered: 10")
    print(f"Total Chunks Processed: {total_chunks_processed}")
    print(f"Average Timeline Calculation Overhead (Per Movie): {(timeline_calc_time / 10)*1000:.2f} ms")
    print(f"Average Chunk Orchestration Latency (Simulated API): {(render_time / total_chunks_processed)*1000:.2f} ms")
    print(f"Average Final Concatenation Overhead (Per Movie): {(concat_time / 10)*1000:.2f} ms")

if __name__ == "__main__":
    run_editor_stress_test()
