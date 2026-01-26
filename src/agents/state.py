from typing import TypedDict, List, Optional, Annotated
from src.models.agent.schemas import ResearchData, ContentStrategy, GeneratedContent
import operator

class AgentState(TypedDict):
    # Inputs
    workflow_id: str
    topic: str
    
    # Internal Work Products
    research_data: Optional[ResearchData]
    strategies: Optional[List[ContentStrategy]]
    selected_strategy_id: Optional[int]
    

    final_content: Optional[GeneratedContent]
    
    error: Optional[str]