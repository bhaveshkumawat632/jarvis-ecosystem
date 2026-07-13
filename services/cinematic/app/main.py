from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.routers import render, telemetry, showbible, autoclip, dashboard

app = FastAPI(
    title="Jarvis Universal Command Center",
    version="3.0.0",
    description="Autonomous AI Text-to-Movie Rendering API"
)

# Allow external frontends (like React/Next.js) to hit the API
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], 
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount the domain routers
app.include_router(render.router, prefix="/api/v1/render", tags=["Production"])
app.include_router(telemetry.router, prefix="/api/v1/telemetry", tags=["Telemetry"])
app.include_router(showbible.router, prefix="/api/v1/showbible", tags=["ShowBible State"])
app.include_router(autoclip.router, prefix="/api/v1/auto-clip", tags=["Auto-Clipper"])
app.include_router(dashboard.router, prefix="/api/v1/dashboard", tags=["Dashboard"])

# Launch instruction (Run this in the terminal):
# cd /home/junglee01/jarvis_universal && uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload


if __name__ == "__main__":
    import uvicorn
    import os
    port = int(os.environ.get("PORT", 8001))
    uvicorn.run("app.main:app", host="0.0.0.0", port=port)
