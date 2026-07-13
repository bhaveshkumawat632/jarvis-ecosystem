from fastapi import APIRouter, HTTPException, BackgroundTasks
from app.api.schemas.workflow import GenerateRequest, GenerateResponse, TaskStatusResponse
from app.core.event_bus import event_bus
from app.core.task_state import task_state
import uuid
import structlog

logger = structlog.get_logger(__name__)
router = APIRouter()

@router.post("/generate", response_model=GenerateResponse)
async def start_generation(req: GenerateRequest, background_tasks: BackgroundTasks):
    task_id = str(uuid.uuid4())
    
    # Initialize state
    await task_state.update_state(task_id, "PENDING", {"topic": req.topic})
    
    # Delegate strictly to EventBus for side-effects
    await event_bus.publish("SYSTEM_TRIGGER_WORKFLOW", payload=req.dict(), task_id=task_id)
    
    # Actually trigger the pipeline in Celery using the specific task_id!
    from workers.celery_worker import generate_video_task
    generate_video_task.apply_async(
        args=[req.topic, req.duration, req.quality],
        task_id=task_id
    )
    
    logger.info("api_workflow_triggered", task_id=task_id, topic=req.topic)
    return GenerateResponse(task_id=task_id, status="accepted", message="Workflow queued for processing")

@router.get("/status/{task_id}", response_model=TaskStatusResponse)
async def get_task_status(task_id: str):
    state_data = await task_state.get_state(task_id)
    if not state_data:
        raise HTTPException(status_code=404, detail="Task not found")
        
    return TaskStatusResponse(
        task_id=task_id,
        state=state_data.get("state", "UNKNOWN"),
        metadata=state_data.get("metadata", {})
    )

@router.post("/cancel/{task_id}")
async def cancel_task(task_id: str):
    await event_bus.publish("SYSTEM_CANCEL_WORKFLOW", payload={}, task_id=task_id)
    return {"status": "cancellation_requested", "task_id": task_id}

@router.post("/retry/{task_id}")
async def retry_task(task_id: str):
    await task_state.update_state(task_id, "RETRYING")
    await event_bus.publish("SYSTEM_RETRY_WORKFLOW", payload={}, task_id=task_id)
    return {"status": "retry_requested", "task_id": task_id}
