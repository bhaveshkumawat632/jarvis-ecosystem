import time
import os
from movie_generator import generate_movie_pipeline, PROJECTS_DIR

def run_master_payload():
    project_id = "chronological_arbitrage_01"
    
    # The high-fidelity thriller payload
    idea = (
        "Chronological Arbitrage: The 1980 Playbook. A tense, high-stakes financial thriller. "
        "A rogue quantitative analyst discovers a temporal loophole in the high-frequency trading algorithms "
        "that allows him to execute trades three seconds in the past. He sits in a dimly lit, server-filled room, "
        "sweating as the monitors glow green with impossible profits, before suited corporate enforcers kick down the glass doors."
    )
    
    print(f"[*] Initiating Master Payload: {project_id}")
    print("[*] Engaging 5-Layer Autonomous Production Engine...")
    start_time = time.time()
    
    try:
        generate_movie_pipeline(
            project_id=project_id,
            idea=idea,
            voice="en-US-GuyNeural",
            music_mood="dramatic"
        )
        end_time = time.time()
        
        output_dir = os.path.join(PROJECTS_DIR, project_id)
        
        print("\n" + "="*60)
        print("🎬 MASTER RENDER COMPLETE")
        print(f"⏱️ Total Production Time: {round(end_time - start_time, 2)} seconds")
        if os.path.exists(output_dir):
            files = os.listdir(output_dir)
            print(f"📁 Master Artifacts Generated: {len(files)} files written to disk.")
        print("="*60)
        
    except Exception as e:
        print(f"\n❌ MASTER PIPELINE FAILURE: {str(e)}")

if __name__ == "__main__":
    run_master_payload()
