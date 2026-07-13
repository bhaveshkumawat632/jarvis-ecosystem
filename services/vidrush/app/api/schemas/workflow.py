from pydantic import BaseModel
from typing import Optional

class GenerateRequest(BaseModel):
    topic: str
    duration: int = 8
    quality: str = "1080p"
    project_id: Optional[str] = "default"

class GenerateResponse(BaseModel):
    task_id: str
    status: str
    message: str

class TaskStatusResponse(BaseModel):
    task_id: str
    state: str
    metadata: Optional[dict] = {}
