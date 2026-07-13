from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from fastapi.security.api_key import APIKeyQuery, APIKeyHeader
import requests
import os
from celery import Celery

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")

API_KEY_NAME = "api_key"
api_key_query = APIKeyQuery(name=API_KEY_NAME, auto_error=False)

SECRET_KEY = os.environ.get("DASHBOARD_SECRET_KEY", "jarvis_junglee")

def get_api_key(request: Request, api_key_query: str = Depends(api_key_query)):
    key = api_key_query
    if key == SECRET_KEY:
        return key
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid API Key",
    )

@router.get("/", response_class=HTMLResponse)
async def dashboard_view(request: Request, api_key: str = Depends(get_api_key)):
    cinematic_health = "Online"
    vidrush_health = "Offline"
    try:
        res = requests.get("http://localhost:8002/health", timeout=2)
        if res.status_code == 200:
            vidrush_health = "Online"
    except Exception:
        pass
        
    autoclipper_health = "Offline"
    try:
        celery_app = Celery(broker='redis://localhost:6379/0')
        insp = celery_app.control.inspect()
        active = insp.active()
        if active:
            autoclipper_health = "Online (Worker Active)"
    except Exception:
        pass

    return templates.TemplateResponse(request, "dashboard.html", {
        "request": request,
        "api_key": api_key,
        "cinematic_health": cinematic_health,
        "vidrush_health": vidrush_health,
        "autoclipper_health": autoclipper_health
    })

@router.post("/trigger_dummy")
async def trigger_dummy(api_key: str = Depends(get_api_key)):
    try:
        celery_app = Celery(broker='redis://localhost:6379/0')
        celery_app.send_task("cinematic.dummy_task")
        return {"status": "success", "message": "Dummy task triggered via Celery."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
