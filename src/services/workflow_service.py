# Find the strategizing_node function and update it:

async def strategizing_node(state: WorkflowState) -> WorkflowState:
    """Generate 3 content strategies from research"""
    print(f"--- ♟️ NODE: STRATEGIZING for '{state.topic}' ---")
    
    research = state.research_data
    
    prompt = f"""
You are a content strategist. Based on this research, generate 3 different content angles.

TOPIC: {state.topic}

RESEARCH SUMMARY:
{research.summary[:2000]}

SOURCES:
{', '.join(research.sources)}

Return ONLY a valid JSON array with this exact structure (no markdown, no explanation):
[
  {{
    "id": 1,
    "angle": "Short title for angle 1",
    "hook": "Opening hook sentence",
    "description": "Why this angle works"
  }},
  {{
    "id": 2,
    "angle": "Short title for angle 2",
    "hook": "Opening hook sentence",
    "description": "Why this angle works"
  }},
  {{
    "id": 3,
    "angle": "Short title for angle 3",
    "hook": "Opening hook sentence",
    "description": "Why this angle works"
  }}
]
"""
    
    llm = LLMService()
    raw_response = await llm.generate_content(prompt)
    
    try:
        # Try parsing directly
        strategies = json.loads(raw_response)
        
        # Validate structure
        if isinstance(strategies, list) and len(strategies) > 0:
            state.strategies = strategies
            print(f"✅ Generated {len(strategies)} strategies")
        else:
            raise ValueError("Invalid strategy structure")
            
    except Exception as e:
        print(f"⚠️ LLM parsing failed: {e}")
        print(f"Raw response: {raw_response[:500]}")
        
        # FALLBACK: Create default strategies from research
        state.strategies = [
            {
                "id": 1,
                "angle": "Educational Deep Dive",
                "hook": f"Here's what most people miss about {state.topic}...",
                "description": "Break down complex topics with clear insights"
            },
            {
                "id": 2,
                "angle": "Contrarian Take",
                "hook": f"Everyone's wrong about {state.topic}. Here's why:",
                "description": "Challenge common assumptions with data"
            },
            {
                "id": 3,
                "angle": "Actionable Playbook",
                "hook": f"3 steps to leverage {state.topic} today:",
                "description": "Practical, immediately useful advice"
            }
        ]
        print(f"✅ Using fallback strategies")
    
    return state