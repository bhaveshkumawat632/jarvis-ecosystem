import os
from typing import List, Dict, Any
from app.schemas.master_schema import (
    MasterNarrativeSchema,
    MasterManifest,
    TimelineEvent,
    AudioLayer
)

class TimelineGeneratorAgent:
    """
    The TimelineGeneratorAgent sits after the Orchestrator runs the creative agents.
    It consumes the validated MasterNarrativeSchema and calculated asset durations,
    and outputs a strict Timecode Metadata Stream (Master Manifest).
    """
    
    def __init__(self):
        pass

    def generate_manifest(self, 
                          project_id: str, 
                          narrative: MasterNarrativeSchema, 
                          scene_assets: List[Dict[str, Any]]) -> MasterManifest:
        """
        Builds the MasterManifest by iterating through scenes, calculating cumulative 
        time offsets, and assigning exact temporal coordinates for audio and visuals.
        
        Args:
            project_id: Unique ID for the project.
            narrative: The validated MasterNarrativeSchema containing Director, Emotion, and SEO outputs.
            scene_assets: A list of dicts containing the actual generated files and durations, e.g.:
                [
                    {
                        "scene_number": 1, 
                        "duration": 4.15, 
                        "video_path": "/path/v1.mp4", 
                        "audio_path": "/path/a1.wav",
                        "script_text": "This is scene 1."
                    }, ...
                ]
        """
        events: List[TimelineEvent] = []
        current_time_offset = 0.0
        
        # Determine global music parameters based on Director's mandate
        music_target_level = 0.2
        if narrative.director_mandate and narrative.director_mandate.pace == "fast":
            music_target_level = 0.35
            
        emotion_desc = "neutral"
        if narrative.emotion_profile:
            emotion_desc = narrative.emotion_profile.emotion

        for idx, scene in enumerate(scene_assets):
            scene_id = f"scene_{scene['scene_number']:02d}"
            duration = scene["duration"]
            
            # Construct Audio Layers for this specific event window
            audio_layers = []
            
            # 1. Voiceover Track (Primary)
            audio_layers.append(AudioLayer(
                track_type="VOICEOVER",
                file_path=scene.get("audio_path"),
                gain_reduction_needed=False,
                target_level=1.0,
                fade_in=0.0,
                fade_out=0.0
            ))
            
            # 2. Music Track (Background/Ducking)
            # The music track overlaps, but we define its behavior *within* this timecode block.
            # Because voiceover exists here, music must duck.
            audio_layers.append(AudioLayer(
                track_type="MUSIC",
                file_path="global_music.mp3", # Reference to the global track
                gain_reduction_needed=True,
                target_level=music_target_level,
                fade_in=0.1,  # Fast fade in for ducking adjustments
                fade_out=0.1
            ))
            
            # Create the TimelineEvent
            event = TimelineEvent(
                event_id=scene_id,
                start_time_offset=round(current_time_offset, 3),
                duration=round(duration, 3),
                visual_source=scene.get("video_path", ""),
                audio_layers=audio_layers,
                script_node=scene.get("script_text", ""),
                emotion_context=emotion_desc
            )
            
            events.append(event)
            current_time_offset += duration

        manifest = MasterManifest(
            project_id=project_id,
            total_duration=round(current_time_offset, 3),
            events=events
        )
        
        return manifest

if __name__ == "__main__":
    # Test execution
    from app.schemas.master_schema import DirectorOutput, EmotionOutput
    
    dummy_narrative = MasterNarrativeSchema(
        topic="Cyberpunk Tea",
        director_mandate=DirectorOutput(emotion="curiosity", pace="slow", music="ambient", style="documentary"),
        emotion_profile=EmotionOutput(emotion="curiosity", suggested_color="blue", zoom_effect="slow_in")
    )
    
    dummy_assets = [
        {"scene_number": 1, "duration": 5.25, "video_path": "vid1.mp4", "audio_path": "aud1.wav", "script_text": "Neon lights."},
        {"scene_number": 2, "duration": 3.80, "video_path": "vid2.mp4", "audio_path": "aud2.wav", "script_text": "Steam rises."}
    ]
    
    agent = TimelineGeneratorAgent()
    manifest = agent.generate_manifest("proj_001", dummy_narrative, dummy_assets)
    print(manifest.model_dump_json(indent=4))
