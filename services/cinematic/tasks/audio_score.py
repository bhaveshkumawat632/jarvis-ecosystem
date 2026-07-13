import os
import torch
from celery import Celery
import scipy.io.wavfile as wavfile

app = Celery('cinematic.audio_score', broker='redis://localhost:6379/0', backend='redis://localhost:6379/0')

@app.task(bind=True, name="task.generate_audio_score")
def generate_audio_score(self, prompt, duration_seconds, project_dir):
    """
    Phase 35 Local Composer Node.
    Uses Meta's MusicGen to dynamically score the project.
    """
    print(f"[*] Celery Worker: Initializing MusicGen for prompt: '{prompt}'")
    output_path = os.path.join(project_dir, "raw_music.wav")
    
    try:
        from audiocraft.models import MusicGen
        
        # Load the model directly into VRAM
        model = MusicGen.get_pretrained('facebook/musicgen-medium')
        model.set_generation_params(duration=duration_seconds)
        
        # Execute the auto-regressive tensor generation
        print(f"[*] Generating {duration_seconds}s of score...")
        wav_tensor = model.generate([prompt])
        
        # The generated tensor is [B, C, T]
        audio_data = wav_tensor[0, 0].cpu().numpy()
        sample_rate = model.sample_rate
        
        wavfile.write(output_path, sample_rate, audio_data)
        print(f"[+] Audio score generated successfully: {output_path}")
        
    except Exception as e:
        print(f"[-] MusicGen initialization or execution failed: {e}")
        output_path = None
        
    finally:
        # CRITICAL: Purge the VRAM to ensure PyTorch and ComfyUI have full headroom
        if 'model' in locals():
            del model
        torch.cuda.empty_cache()
        print("[*] MusicGen flushed from VRAM.")

    return {"status": "success", "asset_path": output_path}
