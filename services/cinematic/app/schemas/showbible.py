from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime

class SceneState(BaseModel):
    scene_id: str
    project_id: str
    scene_number: int
    prompt_visual: str
    voice_audio_path: Optional[str] = None
    music_audio_path: Optional[str] = None
    render_video_path: Optional[str] = None
    status: str
    error_log: Optional[str] = None

class ProjectDetailResponse(BaseModel):
    project_id: str
    concept: str
    status: str
    created_at: str
    scenes: List[SceneState]

class ProjectSummary(BaseModel):
    project_id: str
    concept: str
    status: str
    created_at: str
