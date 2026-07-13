from pydantic import BaseModel, Field

class ConceptRequest(BaseModel):
    user_concept: str = Field(..., description="The core narrative prompt for the movie.")
    resolution: str = Field("2048x1152", description="Target export resolution.")

class ProductionResponse(BaseModel):
    project_id: str
    status: str
    message: str
