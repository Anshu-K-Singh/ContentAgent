from sqlalchemy import Column, String, JSON, DateTime, Enum as SQLEnum
from sqlalchemy.dialects.sqlite import BLOB
import uuid
from datetime import datetime
from src.core.database import Base
from src.models.agent.schemas import WorkflowStatus

class WorkflowTable(Base):
    __tablename__ = "agent_workflows"

    # Use String for UUID in SQLite as it doesn't support native UUID
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    topic = Column(String, nullable=False)
    
    status = Column(String, default=WorkflowStatus.RESEARCHING.value)
    research_data = Column(JSON, nullable=True)
    strategies = Column(JSON, nullable=True) # List of dicts
    selected_strategy_id = Column(String, nullable=True)
    final_content = Column(JSON, nullable=True)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)