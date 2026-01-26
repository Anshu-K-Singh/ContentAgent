import json
import re  # Add this import
from src.agents.state import AgentState
from src.services.research_service import ResearchService
from src.services.llm_service import LLMService
from src.repos.agent.workflow_repo import WorkflowRepo
from src.models.agent.schemas import ResearchData, ContentStrategy, GeneratedContent, WorkflowStatus
from src.core.database import AsyncSessionLocal

# Initialize Services
researcher = ResearchService()
llm = LLMService()

async def research_node(state: AgentState) -> AgentState:
    """
    1. Search the web.
    2. Synthesize a brief.
    3. Save to DB.
    """
    print(f"--- 🕵️ NODE: RESEARCHING '{state['topic']}' ---")
    
    # 1. Execute Research
    raw_data = await researcher.search_web(state['topic'])

    print(f"🔍 Raw Data: {raw_data}...")
    
    # 2. Use LLM to clean up the summary (optional, but better quality)
    prompt = f"""
    You are a Research Assistant. Summarize these raw search results into a clean, executive brief for a content creator.
    
    Raw Results:
    {raw_data.summary}
    
    Format: JSON with keys 'summary' (str), 'key_points' (list[str]).
    """
    try:
        # We use Flash for speed/cost here
        llm_response = await llm.generate_content(prompt, model="flash")
        # Clean markdown ```json ... ``` if present
        clean_json = llm_response.replace("```json", "").replace("```", "").strip()
        parsed = json.loads(clean_json)
        
        refined_data = ResearchData(
            summary=parsed.get("summary", raw_data.summary),
            sources=raw_data.sources,
            key_points=parsed.get("key_points", raw_data.key_points)
        )
    except Exception as e:
        print(f"⚠️ LLM parsing failed, using raw data: {e}")
        refined_data = raw_data

    # 3. Sync to DB
    async with AsyncSessionLocal() as db:
        repo = WorkflowRepo(db)
        await repo.save_research(state['workflow_id'], refined_data)
    
    return {"research_data": refined_data}

async def strategy_node(state: AgentState) -> AgentState:
    """
    1. Read approved research.
    2. Generate 3 angles.
    3. Save to DB.
    """
    print("--- ♟️ NODE: STRATEGIZING ---")
    
    # If user edited the research, it will be in state['research_data']
    brief = state['research_data']
    
    prompt = f"""
    Based on this research:
    {brief.summary}
    
    User Corrections/Notes:
    {brief.user_feedback or "None"}
    
    Generate 3 distinct content angles for LinkedIn/Twitter.
    1. Educational/How-to
    2. Contrarian/Hot-take
    3. Personal/Storytelling
    
    Return ONLY JSON list of objects: [{{ "id": 1, "angle": "...", "hook": "...", "description": "..." }}]
    """
    
    response = await llm.generate_content(prompt, model="pro")
    clean_json = response.replace("```json", "").replace("```", "").strip()
    
    try:
        strategies_list = json.loads(clean_json)
        strategies = [ContentStrategy(**s) for s in strategies_list]
    except:
        # Fallback if JSON fails
        strategies = []
        print("❌ Strategy JSON parsing failed")

    # Sync to DB
    async with AsyncSessionLocal() as db:
        repo = WorkflowRepo(db)
        await repo.save_strategies(state['workflow_id'], strategies)
        
    return {"strategies": strategies}



# Update src/agents/nodes.py

from src.services.media_service import MediaService  # <--- Import this
# ... (other imports remain)

# Initialize
media_service = MediaService()

async def drafting_node(state: AgentState) -> AgentState:
    print("--- ✍️ NODE: DRAFTING ---")
    
    # 1. Get the Selection
    selected_id = int(state['selected_strategy_id']) # Ensure int
    strategies = state['strategies']
    
    # Find the matching strategy
    selected_strategy = next((s for s in strategies if s.id == selected_id), None)
    
    if not selected_strategy:
        print(f"❌ Error: Strategy ID {selected_id} not found in {strategies}")
        return {"error": "Selected strategy not found"}

    # 2. Generate Text
    prompt = f"""
    You are a professional Ghostwriter. 
    Write a high-viral LinkedIn Post and a Twitter Thread based on:
    
    ANGLE: {selected_strategy.angle}
    HOOK: {selected_strategy.hook}
    CONTEXT: {selected_strategy.description}
    
    RESEARCH DATA:
    {state['research_data'].summary}
    
    OUTPUT FORMAT:
    Return JSON with keys: "linkedin_post", "twitter_thread" (list of strings), "image_prompt".
    """
    
    response = await llm.generate_content(prompt, model="pro")
    
    # JSON Parsing Logic
    try:
        clean_json = response.replace("```json", "").replace("```", "").strip()
        print(f"LLM Drafting Response: {clean_json}")
        
        # Extract JSON object using regex
        json_match = re.search(r'\{.*\}', clean_json, re.DOTALL)
        if json_match:
            clean_json = json_match.group(0)
        
        data = json.loads(clean_json)
    except Exception as e:
        print(f"❌ JSON Parse Error: {e}")
        # Fallback if LLM fails
        data = {
            "linkedin_post": "Error generating post.",
            "twitter_thread": [],
            "image_prompt": "Abstract technology background"
        }

    # 3. Generate Image
    image_url = await media_service.generate_image_url(data.get('image_prompt', 'tech'))
    
    # 4. Construct Final Object
    final_content = GeneratedContent(
        linkedin_post=data.get('linkedin_post'),
        twitter_thread=data.get('twitter_thread'),
        image_prompt=data.get('image_prompt'),
        image_url=image_url
    )
    
    # 5. Save to DB
    async with AsyncSessionLocal() as db:
        repo = WorkflowRepo(db)
        await repo.save_final_content(state['workflow_id'], final_content)

    return {"final_content": final_content}