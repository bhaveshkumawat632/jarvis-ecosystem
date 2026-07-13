from fastapi import APIRouter, HTTPException
import uuid
from app.schemas.autoclip import AutoClipRequest, AutoClipResponse
from celery import Celery
celery_app = Celery(broker="redis://redis:6379/0")

router = APIRouter()

@router.post("/generate", response_model=AutoClipResponse)
def trigger_auto_clipper(request: AutoClipRequest):
    """
    Ingests a YouTube URL and dispatches the 5-step viral clipping pipeline to Celery.
    """
    try:
        # Generate a unique hash for the clipping project
        project_id = f"clip_{uuid.uuid4().hex[:8]}"
        
        # Dispatch to the Celery worker queue
        celery_app.send_task("autoclipper.process_viral_clip", args=[project_id, str(request.youtube_url)])

        return AutoClipResponse(
            project_id=project_id,
            status="QUEUED",
            message="YouTube URL ingested. Auto-Clipper worker dispatched."
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Clipper Pipeline Error: {str(e)}")
