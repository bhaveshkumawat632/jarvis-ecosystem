import os
import sqlite3
from fastapi import APIRouter, HTTPException
from app.schemas.showbible import ProjectDetailResponse, ProjectSummary, SceneState
from typing import List

router = APIRouter()

from jarvis_core_lib.database import get_db_connection

@router.get("/projects", response_model=List[ProjectSummary])
def list_all_projects():
    """Fetches a high-level summary list of all projects inside the studio registry."""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        cursor.execute(
            "SELECT project_id, concept, status, created_at FROM projects ORDER BY created_at DESC"
        )
        rows = cursor.fetchall()
        return [dict(row) for row in rows]
    except sqlite3.Error as e:
        raise HTTPException(status_code=500, detail=f"Query Execution Error: {str(e)}")
    finally:
        conn.close()

@router.get("/project/{project_id}", response_model=ProjectDetailResponse)
def get_project_details(project_id: str):
    """
    Retrieves the complete state configuration for a single project,
    including an embedded array of all corresponding scene entities.
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        # 1. Retrieve the parent project row
        cursor.execute(
            "SELECT project_id, concept, status, created_at FROM projects WHERE project_id = ?",
            (project_id,)
        )
        project_row = cursor.fetchone()
        
        if not project_row:
            raise HTTPException(status_code=404, detail=f"Project ID {project_id} not found.")
            
        # 2. Retrieve all child scenes mapped to this project
        cursor.execute(
            """SELECT scene_id, project_id, scene_number, prompt_visual, 
                      voice_audio_path, music_audio_path, render_video_path, status, error_log 
               FROM scenes WHERE project_id = ? ORDER BY scene_number ASC""",
            (project_id,)
        )
        scene_rows = cursor.fetchall()
        
        scenes_list = [dict(row) for row in scene_rows]
        project_data = dict(project_row)
        project_data["scenes"] = scenes_list
        
        return project_data
        
    except sqlite3.Error as e:
        raise HTTPException(status_code=500, detail=f"Relational Query Error: {str(e)}")
    finally:
        conn.close()
