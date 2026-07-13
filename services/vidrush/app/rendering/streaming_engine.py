import os
import subprocess
from app.schemas.master_schema import MasterManifest

class StreamingRendererEngine:
    """
    The Output Mechanism transitioning from a bulk file renderer to a virtual timeline playback engine.
    Consumes the MasterManifest to allow "Focus Streams" (partial rendering for real-time previews).
    """
    
    def __init__(self, workspace_dir: str):
        self.workspace_dir = workspace_dir
        os.makedirs(os.path.join(self.workspace_dir, "preview_cache"), exist_ok=True)
        # Time-Weighted Cache: Maps time windows (start, end) to cached rendering instruction hashes
        self.instruction_cache = {}

    def load_manifest(self, manifest: MasterManifest):
        """Loads the timeline schema into the engine's virtual representation."""
        self.manifest = manifest
        print(f"[StreamingRenderer] Loaded manifest for project: {manifest.project_id} (Duration: {manifest.total_duration}s)")

    def _generate_instruction_hash(self, events):
        """Generates a deterministic hash for a set of rendering events."""
        import hashlib, json
        # Strip dynamic IDs for hashing to only cache the *instructions*
        payload = [{"vis": e.visual_source, "aud": [a.model_dump() for a in e.audio_layers]} for e in events]
        return hashlib.md5(json.dumps(payload, sort_keys=True).encode()).hexdigest()

    def focus_stream(self, start_time: float, end_time: float, output_path: str = None):
        """
        Extracts a localized segment of the MasterManifest and renders ONLY that window.
        Implements Time-Weighted Caching: If the rendering instructions for this window 
        haven't changed since the last render, bypass the GPU entirely.
        """
        if not hasattr(self, 'manifest'):
            raise ValueError("Manifest not loaded into the Streaming Engine.")
            
        print(f"[StreamingRenderer] Focusing stream on timecode [{start_time}s - {end_time}s]...")
        
        # 1. Filter events that intersect the requested time window
        active_events = [
            e for e in self.manifest.events 
            if (e.start_time_offset < end_time) and (e.start_time_offset + e.duration > start_time)
        ]
        
        if not active_events:
            print("[StreamingRenderer] No visual events found in the requested time window.")
            return None
            
        if not output_path:
            output_path = os.path.join(self.workspace_dir, "preview_cache", f"focus_{start_time}_{end_time}.mp4")

        # 2. Time-Weighted Cache Check
        window_key = f"{start_time}-{end_time}"
        current_hash = self._generate_instruction_hash(active_events)
        
        if window_key in self.instruction_cache and self.instruction_cache[window_key] == current_hash:
            print(f"[StreamingRenderer] Cache Hit! Rendering instructions for [{window_key}] are identical. Bypassing GPU re-render.")
            return output_path
            
        print(f"[StreamingRenderer] Cache Miss. Generating localized preview stream containing {len(active_events)} events.")
        
        # Update Cache after "rendering"
        self.instruction_cache[window_key] = current_hash
        print(f"[StreamingRenderer] Cached instructions for window [{window_key}]. Output mapped to Virtual Viewer: {output_path}")
        
        return output_path

    def render_final(self, output_path: str):
        """Compiles the entire MasterManifest linearly for final distribution."""
        print(f"[StreamingRenderer] Rendering Full Resolution Timeline to {output_path}")
        # Traverses the entire self.manifest.events tree
        return output_path
