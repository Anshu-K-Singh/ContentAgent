# test_agent.py
import asyncio
from src.agents.graph import research_app
from src.core.database import engine, Base

async def test():
    # --- FIX: Create Tables First ---
    print("🛠️ Initializing Database...")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    # Mock inputs
    inputs = {"workflow_id": "test-123", "topic": "trump maduro"}
    
    print("🚀 Starting Research Graph...")
    # Trigger the agent
    result = await research_app.ainvoke(inputs)
    
    # Print the summary found
    if result.get('research_data'):
        print("✅ Result:", result['research_data'])
    else:
        print("❌ No research data found.")

if __name__ == "__main__":
    asyncio.run(test())