import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))))

from fastapi import APIRouter, HTTPException
from app.schemas.production import ConceptRequest, ProductionResponse
from narrative_agent import HybridNarrativeAgent

router = APIRouter()

@router.post("/generate", response_model=ProductionResponse)
def trigger_movie_generation(request: ConceptRequest):
    """
    Ingests a prompt, queries NVIDIA NIM, populates SQLite, 
    and drops the heavy render payload into the Celery worker queue.
    """
    try:
        agent = HybridNarrativeAgent()
        
        # The agent queries the cloud and dispatches the Celery jobs internally
        script_data = agent.run(request.user_concept)
        project_id = script_data.get("project_id", "unknown_project")
        
        return ProductionResponse(
            project_id=project_id,
            status="QUEUED",
            message="NIM JSON validated. Background rendering dispatched to Celery."
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Pipeline Error: {str(e)}")
