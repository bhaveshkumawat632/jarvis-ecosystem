import time
import os
from movie_generator import generate_movie_pipeline, PROJECTS_DIR

def run_stress_test():
    project_id = "test_cyberpunk_001"
    idea = "A cybernetically enhanced detective examines a glowing neon crime scene in the pouring rain. He discovers a shattered neural drive on the pavement, picks it up, and realizes the serial killer is someone from his own precinct."
    
    print(f"[*] Starting E2E Stress Test for Project: {project_id}")
    start_time = time.time()
    
    try:
        generate_movie_pipeline(
            project_id=project_id,
            idea=idea,
            voice="en-US-GuyNeural",
            music_mood="cinematic"
        )
        end_time = time.time()
        
        output_dir = os.path.join(PROJECTS_DIR, project_id)
        final_file = os.path.join(output_dir, "final_render.mp4") # Adjust filename if your pipeline uses a different default
        
        print("\n" + "="*50)
        print("✅ E2E TEST COMPLETE")
        print(f"⏱️ Total Execution Time: {round(end_time - start_time, 2)} seconds")
        if os.path.exists(output_dir):
            files = os.listdir(output_dir)
            print(f"📁 Generated Artifacts: {', '.join(files)}")
        print("="*50)
        
    except Exception as e:
        print(f"\n❌ E2E TEST FAILED: {str(e)}")

if __name__ == "__main__":
    run_stress_test()
