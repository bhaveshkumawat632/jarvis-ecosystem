from pydantic import BaseModel, HttpUrl

class AutoClipRequest(BaseModel):
    youtube_url: HttpUrl

class AutoClipResponse(BaseModel):
    project_id: str
    status: str
    message: str
