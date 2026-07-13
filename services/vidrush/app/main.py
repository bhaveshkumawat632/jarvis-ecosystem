import asyncio
import structlog
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.core.event_bus import event_bus
from app.core.task_state import task_state
from app.api.routes import workflow, editor
from app.api.websocket import event_stream
from configs.settings import OUTPUT_DIR
from app.core.exceptions import setup_exception_handlers

logger = structlog.get_logger(__name__)

app = FastAPI(title="VidRush Media Platform Control Plane")

setup_exception_handlers(app)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount routes
app.include_router(workflow.router, prefix="/api/v1/workflow", tags=["Workflow"])
app.include_router(editor.router, prefix="/api/v1/editor", tags=["NLE Sandbox"])
app.include_router(event_stream.router, tags=["Realtime"])

@app.get("/health")
async def health_check():
    return {"status": "ok"}


# Mount static outputs
app.mount("/outputs", StaticFiles(directory=OUTPUT_DIR), name="outputs")

@app.on_event("startup")
async def startup_event():
    # Start Event Bus
    event_bus.start()
    
    # Connect Redis State Manager
    await task_state.connect()
    
    logger.info("control_plane_initialized", status="ready")

@app.on_event("shutdown")
async def shutdown_event():
    await event_bus.stop()
    logger.info("control_plane_shutdown")

if __name__ == "__main__":
    import uvicorn
    import os
    port = int(os.environ.get("PORT", 8002))
    uvicorn.run("app.main:app", host="0.0.0.0", port=port)
