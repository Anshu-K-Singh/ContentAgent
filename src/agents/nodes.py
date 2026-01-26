import json
import re
import asyncio  # Add this
from src.agents.state import AgentState
from src.services.research_service import ResearchService
from src.services.llm_service import LLMService
from src.repos.agent.workflow_repo import WorkflowRepo
from src.models.agent.schemas import ResearchData, ContentStrategy, GeneratedContent, WorkflowStatus
from src.core.database import AsyncSessionLocal


researcher = ResearchService()
llm = LLMService()

async def research_node(state: AgentState) -> AgentState:
    print(f"--- 🕵️ NODE: RESEARCHING '{state['topic']}' ---")
    
    raw_data = await researcher.search_web(state['topic'])
    
    prompt = f"""
    You are a Research Assistant. Analyze these search results and extract:
    
    1. A concise executive summary (2-3 paragraphs)
    2. Top 5 key insights/takeaways as bullet points
    
    Raw Results:
    {raw_data.summary}
    
    Return ONLY valid JSON (no markdown, no extra text):
    {{
        "summary": "Your summary here...",
        "key_points": [
            "Point 1",
            "Point 2",
            "Point 3"
        ]
    }}
    """
    
    try:
        llm_response = await llm.generate_content(prompt, model="flash")
        
        # Log what we actually got
        print(f"🔍 Raw LLM Response (first 500 chars): {llm_response[:500]}")
        
        # Clean markdown wrappers
        clean_json = llm_response.replace("```json", "").replace("```", "").strip()
        
        # Extract JSON object using regex as fallback
        json_match = re.search(r'\{.*\}', clean_json, re.DOTALL)
        if json_match:
            clean_json = json_match.group(0)
            print(f"✅ Extracted JSON from response")
        
        # Check if we have valid JSON before parsing
        if not clean_json or clean_json[0] not in ['{', '[']:
            raise ValueError(f"Response doesn't start with JSON: {clean_json[:100]}")
        
        parsed = json.loads(clean_json)
        
        refined_data = ResearchData(
            summary=parsed.get("summary", raw_data.summary),
            sources=raw_data.sources,
            key_points=parsed.get("key_points", raw_data.key_points)
        )
        print(f"✅ Successfully parsed research data")
        
    except Exception as e:
        print(f"⚠️ LLM parsing failed: {e}")
        print(f"📄 Full response was: {llm_response[:1000]}")
        
        # Use raw data as fallback
        refined_data = raw_data
    
    # Save to DB
    async with AsyncSessionLocal() as db:
        repo = WorkflowRepo(db)
        await repo.save_research(state['workflow_id'], refined_data)
    
    return {"research_data": refined_data}

async def strategy_node(state: AgentState) -> AgentState:
    print("--- ♟️ NODE: STRATEGIZING ---")
    
    brief = state['research_data']
    topic = state.get('topic', 'this topic')
    
    # Format key points as bullet list
    key_points_text = "\n".join(f"- {p}" for p in brief.key_points) if brief.key_points else "None"
    
    prompt = f"""
    Based on this research about "{topic}":
    
    KEY INSIGHTS:
    {key_points_text}
    
    FULL CONTEXT:
    {brief.summary[:2000]}
    
    USER CORRECTIONS:
    {brief.user_feedback or "None"}
    
    Generate 3 distinct content angles for LinkedIn/Twitter that leverage these insights:
    1. Educational/How-to
    2. Contrarian/Hot-take
    3. Personal/Storytelling
    
    Return ONLY JSON list: [{{"id": 1, "angle": "...", "hook": "...", "description": "..."}}]
    """
    
    # Retry logic for OpenRouter failures
    max_retries = 2
    strategies = []
    
    for attempt in range(max_retries):
        try:
            response = await llm.generate_content(prompt, model="pro")
            clean_json = response.replace("```json", "").replace("```", "").strip()
            
            # Extract JSON array using regex
            json_match = re.search(r'\[.*\]', clean_json, re.DOTALL)
            if json_match:
                clean_json = json_match.group(0)
            
            strategies_list = json.loads(clean_json)
            strategies = [ContentStrategy(**s) for s in strategies_list]
            
            if len(strategies) > 0:
                print(f"✅ Generated {len(strategies)} strategies on attempt {attempt + 1}")
                break  # Success, exit retry loop
                
        except Exception as e:
            print(f"⚠️ Strategy generation attempt {attempt + 1} failed: {e}")
            if attempt < max_retries - 1:
                print(f"🔄 Retrying...")
                await asyncio.sleep(1)  # Brief delay before retry
            continue
    
    # Fallback if all retries failed
    if not strategies or len(strategies) == 0:
        print("❌ All strategy generation attempts failed, using fallback")
        strategies = [
            ContentStrategy(
                id=1,
                angle="Educational/How-to",
                hook=f"Master {topic}: A practical guide",
                description=f"Break down {topic} into actionable steps that anyone can follow"
            ),
            ContentStrategy(
                id=2,
                angle="Contrarian/Hot-take",
                hook=f"Why everyone misunderstands {topic}",
                description=f"Challenge common misconceptions about {topic} with fresh insights"
            ),
            ContentStrategy(
                id=3,
                angle="Personal/Storytelling",
                hook=f"My unexpected journey with {topic}",
                description=f"Share authentic experiences and lessons learned from {topic}"
            )
        ]
        print(f"✅ Using {len(strategies)} fallback strategies")

    # Sync to DB
    async with AsyncSessionLocal() as db:
        repo = WorkflowRepo(db)
        await repo.save_strategies(state['workflow_id'], strategies)
        print(f"💾 Saved {len(strategies)} strategies to DB")
        
    return {"strategies": strategies}



from src.services.media_service import MediaService  


media_service = MediaService()

async def drafting_node(state: AgentState) -> AgentState:
    print("--- ✍️ NODE: DRAFTING ---")
    
    
    selected_id = int(state['selected_strategy_id']) 
    strategies = state['strategies']
    
    # Find the matching strategy
    selected_strategy = next((s for s in strategies if s.id == selected_id), None)
    
    if not selected_strategy:
        print(f"❌ Error: Strategy ID {selected_id} not found in {strategies}")
        return {"error": "Selected strategy not found"}

    # Generate Text
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
    
    #Construct Final Object
    final_content = GeneratedContent(
        linkedin_post=data.get('linkedin_post'),
        twitter_thread=data.get('twitter_thread'),
        image_prompt=data.get('image_prompt'),
        image_url=image_url
    )
    
    
    async with AsyncSessionLocal() as db:
        repo = WorkflowRepo(db)
        await repo.save_final_content(state['workflow_id'], final_content)

    return {"final_content": final_content}