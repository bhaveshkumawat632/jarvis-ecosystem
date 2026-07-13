from pydantic import BaseModel, Field
from typing import Any, Dict, Optional

class VisualEditRequest(BaseModel):
    color_grade: Optional[str] = Field(None, description="Dropdown selection: e.g., 'Cinematic', 'Teal & Orange', 'Noir'")
    motion_curve_bezier: Optional[str] = Field(None, description="Bezier curve control points as string for camera movement")
    depth_effect_bokeh: Optional[float] = Field(None, ge=0.0, le=1.0, description="Virtual bokeh intensity slider")

class AudioEditRequest(BaseModel):
    ambience_volume_db: Optional[float] = Field(None, description="Adjust background ambience volume in dB (slider)")
    dialogue_focus_ms: Optional[int] = Field(None, description="Increase dialogue focus duration in ms")
    music_ducking_ratio: Optional[float] = Field(None, ge=0.0, le=1.0, description="Ducking aggressiveness slider")

class CharacterEditRequest(BaseModel):
    personality_bias_override: Optional[str] = Field(None, description="Force a specific character personality shift")

class SceneMetadataEditRequest(BaseModel):
    """
    The Request Body Schema mapping frontend widgets to SandboxAgent parameter manipulations.
    """
    project_id: str = Field(..., description="The unique project ID")
    event_id: str = Field(..., description="Target Scene ID in the Manifest (e.g., scene_04)")
    visual_overrides: Optional[VisualEditRequest] = None
    audio_overrides: Optional[AudioEditRequest] = None
    character_overrides: Optional[CharacterEditRequest] = None

class SceneMetadataEditResponse(BaseModel):
    """
    The Response Body indicating success and providing the localized preview stream.
    """
    status: str = Field("success", description="Action result")
    message: str = Field(..., description="User-facing success message")
    updated_event_id: str = Field(..., description="The ID of the modified event")
    preview_stream_url: str = Field(..., description="URL to the localized focus stream containing just this edit")
    manifest_version: str = Field(..., description="Updated version hash of the MasterManifest")
