# src/api/routes.py
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import UUID

from src.core.database import get_db, AsyncSessionLocal  
from src.models.agent.schemas import WorkflowResponse, WorkflowStatus, StartWorkflowRequest, ResearchData, ContentStrategy  # Added ResearchData, ContentStrategy
from src.repos.agent.workflow_repo import WorkflowRepo
from src.agents.graph import research_app, strategy_app, drafting_app

router = APIRouter(prefix="/agent", tags=["Agent"])

# HELPER FUNCTION 
async def get_state_from_db(workflow_id: str):
    async with AsyncSessionLocal() as db:
        repo = WorkflowRepo(db)
        workflow = await repo.get_workflow(workflow_id)
        
        # Convert DB JSON fields back to Pydantic/Dict
        research_data = ResearchData(**workflow.research_data) if workflow.research_data else None
        
        strategies = []
        if workflow.strategies:
            strategies = [ContentStrategy(**s) for s in workflow.strategies]
            
        return {
            "workflow_id": workflow.id,
            "topic": workflow.topic,
            "research_data": research_data,
            "strategies": strategies,
            "selected_strategy_id": int(workflow.selected_strategy_id) if workflow.selected_strategy_id else None
        }



async def run_research_task(workflow_id: str, topic: str):
    """
    Runs the Research Graph -> Updates DB -> Stops
    """
    print(f"🚀 [Task] Starting Research for {workflow_id}")
    inputs = {"workflow_id": workflow_id, "topic": topic}
    # This runs the 'research_node' we defined earlier
    await research_app.ainvoke(inputs)
    print(f"✅ [Task] Research Complete for {workflow_id}")

async def run_strategy_task(workflow_id: str):
    """
    Runs the Strategy Graph -> Updates DB -> Stops
    """
    print(f"🚀 [Task] Starting Strategy Gen for {workflow_id}")
    # Load state from DB so the node has the research data
    initial_state = await get_state_from_db(workflow_id)
    await strategy_app.ainvoke(initial_state)
    print(f"✅ [Task] Strategy Gen Complete for {workflow_id}")

async def run_drafting_task(workflow_id: str):
    """
    Runs Drafting Graph -> Updates DB -> Stops
    """
    print(f"🚀 [Task] Starting Drafting for {workflow_id}")
    # Load state so the node has the selection
    initial_state = await get_state_from_db(workflow_id)
    await drafting_app.ainvoke(initial_state)
    print(f"✅ [Task] Drafting Complete for {workflow_id}")


#  ENDPOINTS

@router.post("/start", response_model=WorkflowResponse)
async def start_workflow(
    request: StartWorkflowRequest, 
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db)
):
   
    repo = WorkflowRepo(db)
    # 1. Create Record
    workflow = await repo.create_workflow(request.topic)
    
    # 2. Trigger Research Background Task
    background_tasks.add_task(run_research_task, workflow.id, request.topic)
    
    # 3. Return immediate response
    return WorkflowResponse(
        id=workflow.id,
        topic=workflow.topic,
        status=WorkflowStatus.RESEARCHING,
        created_at=workflow.created_at
    )

@router.get("/{workflow_id}", response_model=WorkflowResponse)
async def get_workflow_status(
    workflow_id: str,
    db: AsyncSession = Depends(get_db)
):
    
    repo = WorkflowRepo(db)
    workflow = await repo.get_workflow(workflow_id)
    if not workflow:
        raise HTTPException(status_code=404, detail="Workflow not found")
    
    
    return workflow

@router.post("/{workflow_id}/approve-research")
async def approve_research(
    workflow_id: str,
    user_feedback: str = None, # Optional edits
    background_tasks: BackgroundTasks = None,
    db: AsyncSession = Depends(get_db)
):
    repo = WorkflowRepo(db)
    workflow = await repo.get_workflow(workflow_id)
    if not workflow:
        raise HTTPException(status_code=404, detail="Workflow not found")

    
    if workflow.research_data:
        # Load current data
        # If SQLite stores as dict, great. If string, json.loads it.
        current_data = workflow.research_data if isinstance(workflow.research_data, dict) else dict(workflow.research_data)
        
        
        from src.models.agent.schemas import ResearchData
        
        
        if user_feedback:
            current_data['user_feedback'] = user_feedback
            
        research_obj = ResearchData(**current_data)
        await repo.save_research(workflow_id, research_obj)

    
    await repo.update_status(workflow_id, WorkflowStatus.STRATEGIZING)
    
    
    background_tasks.add_task(run_strategy_task, workflow_id)
    
    return {"status": "strategizing"}

@router.post("/{workflow_id}/select-strategy")
async def select_strategy(
    workflow_id: str,
    strategy_id: int,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db)
):
    
    try:
        repo = WorkflowRepo(db)
        await repo.update_status(workflow_id, WorkflowStatus.DRAFTING)
        await repo.save_selection(workflow_id, strategy_id)
        background_tasks.add_task(run_drafting_task, workflow_id)
        return {"status": "drafting"}
    except Exception as e:
        print(f"❌ Error in select-strategy: {e}")
        raise HTTPException(status_code=500, detail=f"Internal error: {str(e)}")