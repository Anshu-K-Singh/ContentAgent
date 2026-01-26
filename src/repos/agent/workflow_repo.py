from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import update
from src.models.agent.tables import WorkflowTable
from src.models.agent.schemas import WorkflowStatus, ResearchData, ContentStrategy, GeneratedContent
import json

class WorkflowRepo:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_workflow(self, topic: str) -> WorkflowTable:
        new_workflow = WorkflowTable(topic=topic, status=WorkflowStatus.RESEARCHING.value)
        self.db.add(new_workflow)
        await self.db.commit()
        await self.db.refresh(new_workflow)
        return new_workflow

    async def get_workflow(self, workflow_id: str) -> WorkflowTable | None:
        result = await self.db.execute(select(WorkflowTable).where(WorkflowTable.id == workflow_id))
        return result.scalars().first()

    async def update_status(self, workflow_id: str, status: WorkflowStatus):
        await self.db.execute(
            update(WorkflowTable)
            .where(WorkflowTable.id == workflow_id)
            .values(status=status.value)
        )
        await self.db.commit()

    async def save_research(self, workflow_id: str, data: ResearchData):
        # SQLAlchemy JSON support handles the dict conversion automatically usually, 
        # but safe to dump to dict
        await self.db.execute(
            update(WorkflowTable)
            .where(WorkflowTable.id == workflow_id)
            .values(
                research_data=data.model_dump(),
                status=WorkflowStatus.WAITING_RESEARCH_APPROVAL.value
            )
        )
        await self.db.commit()

    async def save_strategies(self, workflow_id: str, strategies: list[ContentStrategy]):
        strategy_data = [s.model_dump() for s in strategies]
        await self.db.execute(
            update(WorkflowTable)
            .where(WorkflowTable.id == workflow_id)
            .values(
                strategies=strategy_data,
                status=WorkflowStatus.WAITING_STRATEGY_SELECTION.value
            )
        )
        await self.db.commit()

    async def save_final_content(self, workflow_id: str, content: GeneratedContent):
        await self.db.execute(
            update(WorkflowTable)
            .where(WorkflowTable.id == workflow_id)
            .values(
                final_content=content.model_dump(),
                status=WorkflowStatus.COMPLETED.value
            )
        )
        await self.db.commit()


    # Open src/repos/agent/workflow_repo.py and add this method to the class:

    async def save_selection(self, workflow_id: str, strategy_id: int):
        """
        Saves the user's choice (e.g., Strategy #2) to the DB.
        """
        # We store it as a string or int, matches our Table definition
        await self.db.execute(
            update(WorkflowTable)
            .where(WorkflowTable.id == workflow_id)
            .values(
                selected_strategy_id=str(strategy_id),
                status=WorkflowStatus.DRAFTING.value
            )
        )
        await self.db.commit()