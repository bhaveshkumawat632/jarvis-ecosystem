from pydantic import BaseModel, Field
from typing import List, Optional

class DirectorOutput(BaseModel):
    emotion: str = Field(..., description="Primary emotion mapping (e.g. fear, tension, sadness, excitement, curiosity)")
    pace: str = Field(..., description="Pacing of the video: fast, medium, or slow")
    music: str = Field(..., description="Music style: cinematic, suspense, upbeat, or ambient")
    style: str = Field(..., description="General stylistic approach: documentary, reddit, or fast_paced")

class EmotionOutput(BaseModel):
    emotion: str = Field(..., description="Detected primary emotion")
    suggested_color: str = Field(..., description="Suggested color grading or hue")
    zoom_effect: str = Field(..., description="Suggested camera zoom effect: fast_in, slow_in, or none")

class SEOOutput(BaseModel):
    title: str = Field(..., description="Clickable YouTube title")
    description: str = Field(..., description="Full SEO optimized description")
    hashtags: List[str] = Field(..., description="List of hashtags")
    tags: List[str] = Field(..., description="List of SEO tags")
    best_upload_time: str = Field(..., description="Recommended upload time")

class MasterNarrativeSchema(BaseModel):
    """
    The Single Source of Truth for the entire production pipeline.
    All agents must conform their output to this registry.
    """
    version: str = "1.0.0"
    topic: str
    director_mandate: Optional[DirectorOutput] = None
    hook_script: Optional[str] = None
    full_script: Optional[str] = None
    emotion_profile: Optional[EmotionOutput] = None
    seo_metadata: Optional[SEOOutput] = None

class AudioLayer(BaseModel):
    track_type: str = Field(..., description="MUSIC, VOICEOVER, or SFX")
    file_path: Optional[str] = Field(None, description="Path to the audio asset")
    gain_reduction_needed: bool = Field(False, description="True if ducking is required")
    target_level: float = Field(1.0, description="Volume level (0.0 to 1.0)")
    fade_in: float = Field(0.0, description="Fade in duration in seconds")
    fade_out: float = Field(0.0, description="Fade out duration in seconds")

class TimelineEvent(BaseModel):
    event_id: str = Field(..., description="Unique ID for this event (e.g., scene_01)")
    start_time_offset: float = Field(..., description="Absolute start time in seconds")
    duration: float = Field(..., description="Duration of this event in seconds")
    visual_source: str = Field(..., description="Path or reference to the generated visual asset")
    audio_layers: List[AudioLayer] = Field(default_factory=list, description="Audio mixing instructions for this block")
    script_node: str = Field(..., description="The corresponding section of the script")
    emotion_context: str = Field(..., description="The emotional descriptor for this block")

class MasterManifest(BaseModel):
    """
    The final Timecode Metadata Stream that bypasses traditional sequential rendering.
    The Post-Production Sandbox uses this to assemble the video non-destructively.
    """
    project_id: str
    total_duration: float
    events: List[TimelineEvent] = Field(default_factory=list)
