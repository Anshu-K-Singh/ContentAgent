from pydantic import BaseModel, Field
from typing import List, Optional
from enum import Enum
from datetime import datetime
from uuid import UUID

# 1. Enums for State Management
class WorkflowStatus(str, Enum):
    RESEARCHING = "researching"
    WAITING_RESEARCH_APPROVAL = "waiting_research_approval"
    STRATEGIZING = "strategizing"
    WAITING_STRATEGY_SELECTION = "waiting_strategy_selection"
    DRAFTING = "drafting"
    COMPLETED = "completed"
    FAILED = "failed"

# 2. Research Data Structures
class ResearchData(BaseModel):
    summary: str = Field(..., description="Executive summary of findings")
    sources: List[str] = Field(default_factory=list, description="URLs of sources")
    key_points: List[str] = Field(default_factory=list)
    user_feedback: Optional[str] = None # Stores what the user corrected

# 3. Strategy/Ideation Structures
class ContentStrategy(BaseModel):
    id: int
    angle: str = Field(..., description="e.g., 'Contrarian', 'Educational'")
    hook: str
    description: str

# 4. Final Output Structures
class GeneratedContent(BaseModel):
    linkedin_post: Optional[str] = None
    twitter_thread: Optional[List[str]] = None
    image_prompt: Optional[str] = None
    image_url: Optional[str] = None

# 5. The API Response Model (What the UI sees)
class WorkflowResponse(BaseModel):
    id: UUID
    topic: str
    status: WorkflowStatus
    research_data: Optional[ResearchData] = None
    strategies: Optional[List[ContentStrategy]] = None
    selected_strategy_id: Optional[int] = None
    final_content: Optional[GeneratedContent] = None
    created_at: datetime

class StartWorkflowRequest(BaseModel):
    topic: str = Field(..., description="The topic or prompt for content generation")