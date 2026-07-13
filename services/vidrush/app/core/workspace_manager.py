import os
import structlog
from configs.settings import BASE_DIR

logger = structlog.get_logger(__name__)

class WorkspaceManager:
    def __init__(self):
        self.workspaces_root = os.path.join(BASE_DIR, "workspaces")
        os.makedirs(self.workspaces_root, exist_ok=True)

    def initialize_workspace(self, project_id: str) -> dict:
        """
        Creates completely isolated environments for multi-tenant / agency scaling.
        """
        project_dir = os.path.join(self.workspaces_root, project_id)
        
        paths = {
            "root": project_dir,
            "assets": os.path.join(project_dir, "assets"),
            "outputs": os.path.join(project_dir, "outputs"),
            "temp": os.path.join(project_dir, "temp"),
            "memory": os.path.join(project_dir, "memory.db")
        }
        
        for name, path in paths.items():
            if not path.endswith(".db"):
                os.makedirs(path, exist_ok=True)
                
        logger.info("workspace_initialized", project_id=project_id)
        return paths

    def get_workspace(self, project_id: str) -> dict:
        """Retrieves paths for an existing workspace."""
        project_dir = os.path.join(self.workspaces_root, project_id)
        if not os.path.exists(project_dir):
            return self.initialize_workspace(project_id)
            
        return {
            "root": project_dir,
            "assets": os.path.join(project_dir, "assets"),
            "outputs": os.path.join(project_dir, "outputs"),
            "temp": os.path.join(project_dir, "temp"),
            "memory": os.path.join(project_dir, "memory.db")
        }

workspace_manager = WorkspaceManager()
