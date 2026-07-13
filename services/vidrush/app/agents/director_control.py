import json
from typing import Dict, Any
from app.schemas.master_schema import MasterManifest, MasterNarrativeSchema

class DirectorControlAgent:
    """
    The New Brain of the Unified Control Plane.
    Acts as the centralized state manager, interpreting subjective user intent 
    against the established schema and translating it into quantifiable timeline modifications.
    """
    def __init__(self):
        pass

    def apply_directive(self, 
                        manifest: MasterManifest, 
                        narrative: MasterNarrativeSchema, 
                        user_command: str) -> MasterManifest:
        """
        Translates abstract user commands (e.g., 'Make the pacing feel more anxious') 
        into technical adjustments within the MasterManifest.
        """
        print(f"[DirectorControlAgent] Analyzing command: '{user_command}'")
        
        # Conceptual translation matrix (In a full implementation, this uses an LLM to map intent)
        # Here we simulate translating subjective adjectives into quantifiable data.
        if "anxious" in user_command.lower() or "tension" in user_command.lower():
            print("[DirectorControlAgent] Intent Mapping -> Anxious/Tension")
            # Update the Narrative Schema state
            if narrative.director_mandate:
                narrative.director_mandate.pace = "fast"
                narrative.director_mandate.emotion = "tension"
            
            # Apply quantifiable adjustments to the Manifest
            for event in manifest.events:
                event.emotion_context = "tension"
                for audio in event.audio_layers:
                    if audio.track_type == "MUSIC":
                        audio.target_level = min(1.0, audio.target_level * 1.5) # Boost music volume
                        audio.fade_in = 0.05 # Harsher audio cuts
                        
        elif "drama" in user_command.lower() and "middle" in user_command.lower():
            print("[DirectorControlAgent] Intent Mapping -> Drama boost in Middle Section")
            # Isolate the middle section based on timestamps
            mid_start = manifest.total_duration * 0.3
            mid_end = manifest.total_duration * 0.7
            
            for event in manifest.events:
                if mid_start <= event.start_time_offset <= mid_end:
                    event.emotion_context = "drama"
                    for audio in event.audio_layers:
                        if audio.track_type == "VOICEOVER":
                            audio.target_level = 1.2 # Boost dialogue presence
                            
        # The agent maintains a feedback loop with the self-critic (mocked here)
        self._validate_feasibility(manifest)
        
        return manifest
        
    def _validate_feasibility(self, manifest: MasterManifest):
        """Simulates checking with the Self-CriticAgent to ensure edits don't break the timeline."""
        for event in manifest.events:
            for audio in event.audio_layers:
                if audio.target_level > 2.0:
                    print(f"[Warning] Audio level capped to prevent clipping in event {event.event_id}")
                    audio.target_level = 2.0
