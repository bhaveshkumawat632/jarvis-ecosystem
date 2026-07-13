import asyncio
import os
from fastapi import APIRouter, Request
from fastapi.responses import StreamingResponse
import redis.asyncio as redis

router = APIRouter()

from jarvis_core_lib.redis_client import get_redis_client

async def progress_streamer(request: Request, project_id: str):
    """
    Subscribes to the Redis Pub/Sub channel and yields SSE formatted strings.
    """
    redis_client = get_redis_client()
    pubsub = redis_client.pubsub()
    channel_name = f"telemetry:{project_id}"
    
    await pubsub.subscribe(channel_name)
    
    try:
        while True:
            # Drop the connection immediately if the browser tab is closed
            if await request.is_disconnected():
                print(f"[*] Client disconnected from telemetry stream: {project_id}")
                break
            
            # Poll Redis for new telemetry broadcasts
            message = await pubsub.get_message(ignore_subscribe_messages=True, timeout=0.5)
            
            if message:
                payload = message['data']
                # SSE standard strictly requires 'data: <string>\n\n'
                yield f"data: {payload}\n\n"
                
                # Graceful termination trigger
                if '"status": "COMPLETED"' in payload or '"status": "FAILED"' in payload:
                    break
                    
            # Yield control back to the ASGI event loop to handle other requests
            await asyncio.sleep(0.1)
            
    finally:
        await pubsub.unsubscribe(channel_name)
        await redis_client.aclose()

@router.get("/stream/{project_id}")
async def stream_telemetry(request: Request, project_id: str):
    """
    The Server-Sent Events (SSE) endpoint for the UI to consume.
    """
    return StreamingResponse(
        progress_streamer(request, project_id), 
        media_type="text/event-stream"
    )
