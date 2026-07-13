import os
import time
from movie_generator import apply_tensor_super_resolution_comfy
import subprocess

def test_phase33():
    project_dir = "/home/junglee01/jarvis_universal"
    input_video = os.path.join(project_dir, "A_Scientist_Discovers_Time_Tra_1080pTEMP_MPY_wvf_snd.mp4")
    
    if not os.path.exists(input_video):
        print("[-] Sample video not found for testing.")
        return
        
    print(f"[*] Testing Phase 33 Upscale on: {input_video}")
    start_time = time.time()
    
    output_video = apply_tensor_super_resolution_comfy(project_dir, input_video)
    
    end_time = time.time()
    
    print(f"[*] Time taken: {end_time - start_time:.2f} seconds")
    
    if os.path.exists(output_video) and output_video != input_video:
        print("[+] Upscale successful. Verifying output format...")
        subprocess.run(["ffprobe", "-v", "error", "-select_streams", "v:0", "-show_entries", "stream=codec_name,width,height,pix_fmt", "-of", "default=noprint_wrappers=1", output_video])
    else:
        print("[-] Upscale failed or fell back to original video.")

if __name__ == "__main__":
    test_phase33()
