import os
import math
import numpy as np
import cv2
import scipy.io.wavfile as wavfile
import subprocess

def get_audio_envelope(audio_path, fps=30):
    """
    Computes the volume amplitude envelope of an audio file, 
    downsampled and smoothed to match the target video frame rate.
    """
    try:
        if not os.path.exists(audio_path):
            print(f"[-] Audio path missing for envelope extraction: {audio_path}")
            return None
            
        sample_rate, data = wavfile.read(audio_path)
        
        # Convert stereo to mono
        if len(data.shape) > 1:
            data = data.mean(axis=1)
            
        # Normalize audio signal to range [-1.0, 1.0]
        data = data.astype(np.float32)
        max_val = np.max(np.abs(data))
        if max_val > 0:
            data = data / max_val
            
        # Calculate samples per video frame
        samples_per_frame = int(sample_rate / fps)
        envelope = []
        
        for i in range(0, len(data), samples_per_frame):
            chunk = data[i:i + samples_per_frame]
            if len(chunk) == 0:
                break
            # Use root mean square (RMS) for signal amplitude
            rms = np.sqrt(np.mean(np.square(chunk)))
            envelope.append(rms)
            
        # Smooth the volume envelope using a moving average filter
        kernel_size = 5
        if len(envelope) >= kernel_size:
            smoothed = np.convolve(envelope, np.ones(kernel_size)/float(kernel_size), mode='same')
        else:
            smoothed = np.array(envelope)
            
        # Normalize envelope to [0.0, 1.0]
        max_env = np.max(smoothed) if len(smoothed) > 0 else 1.0
        if max_env > 0:
            smoothed = smoothed / max_env
            
        return smoothed
    except Exception as e:
        print(f"[-] Failed to extract audio envelope: {str(e)}")
        return None

def run_local_wav2lip(video_path, audio_path, output_path):
    """
    Attempts to run local Wav2Lip inference using PyTorch or model scripts.
    Checks if Wav2Lip workspace is available and runs inside the container.
    """
    wav2lip_dir = "/workspace/Wav2Lip"
    checkpoint_path = "/workspace/models/wav2lip_gan.pth"
    
    if os.path.exists(wav2lip_dir) and os.path.exists(checkpoint_path):
        print("[*] Local Wav2Lip workspace detected. Initiating deep neural face alignment...")
        cmd = [
            "python3", f"{wav2lip_dir}/inference.py",
            "--checkpoint", checkpoint_path,
            "--face", video_path,
            "--audio", audio_path,
            "--outfile", output_path
        ]
        try:
            res = subprocess.run(cmd, capture_output=True, text=True, check=True)
            if os.path.exists(output_path) and os.path.getsize(output_path) > 1000:
                print("[+] Local neural Wav2Lip inference completed successfully.")
                return True
            else:
                print(f"[-] Wav2Lip failed to create file. Output: {res.stdout}")
        except Exception as e:
            print(f"[-] Wav2Lip subprocess failed: {str(e)}")
    else:
        print("[*] Local Wav2Lip checkpoints or scripts not found. Falling back to local DSP warping engine.")
    return False

def amplitude_driven_mouth_warp(video_path, audio_path, output_path):
    """
    Applies standard DSP mouth warping to simulate speech movements.
    Detections are scaled by volume amplitude to align with audio beats.
    """
    print(f"[*] Commencing amplitude-driven facial warp fallback on: {video_path}")
    
    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        print(f"[-] Error: Failed to open video source: {video_path}")
        return video_path
        
    fps = cap.get(cv2.CAP_PROP_FPS)
    if fps <= 0:
        fps = 30.0
    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    
    # Extract audio volume profile
    envelope = get_audio_envelope(audio_path, fps)
    
    # Initialize frontal face cascade detector
    cascade_path = cv2.data.haarcascades + 'haarcascade_frontalface_default.xml'
    face_cascade = cv2.CascadeClassifier(cascade_path)
    
    # Prepare video writer (h264 structure fallback)
    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    out_temp = output_path + ".temp.mp4"
    out = cv2.VideoWriter(out_temp, fourcc, fps, (width, height))
    
    frame_idx = 0
    while True:
        ret, frame = cap.read()
        if not ret:
            break
            
        vol = envelope[frame_idx] if (envelope is not None and frame_idx < len(envelope)) else 0.0
        
        # Performance optimization: run gray downscaling
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        faces = face_cascade.detectMultiScale(gray, scaleFactor=1.15, minNeighbors=5, minSize=(80, 80))
        
        if len(faces) > 0:
            # Pick largest detected face
            faces = sorted(faces, key=lambda f: f[2]*f[3], reverse=True)
            x, y, w, h = faces[0]
            
            # Predict bounding box for mouth (lower-central face quadrant)
            mouth_w = int(w * 0.38)
            mouth_h = int(h * 0.18)
            mouth_x = x + int(w * 0.31)
            mouth_y = y + int(h * 0.71)
            
            # Warp factors (maximum 25% height elongation)
            warp_factor = 1.0 + (vol * 0.25)
            y_offset = int((mouth_h * warp_factor - mouth_h) / 2.0)
            
            if warp_factor > 1.001 and mouth_y + mouth_h < height and mouth_x + mouth_w < width:
                try:
                    mouth_roi = frame[mouth_y:mouth_y+mouth_h, mouth_x:mouth_x+mouth_w]
                    new_h = int(mouth_h * warp_factor)
                    
                    # Vertical resize stretch
                    warped_mouth = cv2.resize(mouth_roi, (mouth_w, new_h), interpolation=cv2.INTER_LINEAR)
                    
                    # Create linear feathering/blend mask to avoid sharp seams
                    mask = np.zeros((new_h, mouth_w, 3), dtype=np.float32)
                    feather_zone = max(2, int(new_h * 0.18))
                    for r in range(new_h):
                        if r < feather_zone:
                            alpha = r / float(feather_zone)
                        elif r > new_h - feather_zone:
                            alpha = (new_h - r) / float(feather_zone)
                        else:
                            alpha = 1.0
                        mask[r, :] = alpha
                        
                    target_y1 = max(0, mouth_y - y_offset)
                    target_y2 = min(height, target_y1 + new_h)
                    actual_new_h = target_y2 - target_y1
                    
                    if actual_new_h > 0:
                        mask_sliced = mask[0:actual_new_h, :]
                        warped_sliced = warped_mouth[0:actual_new_h, :]
                        
                        bg_roi = frame[target_y1:target_y2, mouth_x:mouth_x+mouth_w].astype(np.float32)
                        fg_roi = warped_sliced.astype(np.float32)
                        
                        # Alpha blend interpolation
                        blended = mask_sliced * fg_roi + (1.0 - mask_sliced) * bg_roi
                        frame[target_y1:target_y2, mouth_x:mouth_x+mouth_w] = blended.astype(np.uint8)
                except Exception as ex:
                    # Ignore warp errors and write original frame to safeguard render continuity
                    pass
                    
        out.write(frame)
        frame_idx += 1
        
    cap.release()
    out.release()
    
    # remux audio to output_path using FFmpeg to preserve dialog
    ffmpeg_cmd = [
        "ffmpeg", "-y", "-i", out_temp, "-i", audio_path,
        "-c:v", "copy", "-c:a", "aac", "-map", "0:v:0", "-map", "1:a:0",
        output_path
    ]
    try:
        subprocess.run(ffmpeg_cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True)
        if os.path.exists(out_temp):
            os.remove(out_temp)
        return output_path
    except Exception as e:
        print(f"[-] Remux failed: {str(e)}. Returning visual-only file.")
        if os.path.exists(out_temp):
            os.rename(out_temp, output_path)
        return output_path

def run_lip_sync_pipeline(video_path, audio_path, output_path):
    """
    Core entry point coordinating local lip sync operations.
    Attempts Wav2Lip deep learning, then falls back to OpenCV warp.
    """
    if not os.path.exists(video_path):
        print(f"[-] Input video path does not exist: {video_path}")
        return video_path
    if not os.path.exists(audio_path):
        print(f"[-] Input audio path does not exist: {audio_path}")
        return video_path
        
    # Attempt neural model first
    success = run_local_wav2lip(video_path, audio_path, output_path)
    if success:
        return output_path
        
    # Fallback to local DSP warp
    return amplitude_driven_mouth_warp(video_path, audio_path, output_path)

if __name__ == "__main__":
    import sys
    if len(sys.argv) < 4:
        print("Usage: python3 lip_sync_orchestrator.py <video_path> <audio_path> <output_path>")
    else:
        run_lip_sync_pipeline(sys.argv[1], sys.argv[2], sys.argv[3])
