from langgraph.graph import StateGraph, END
from src.agents.state import AgentState
from src.agents.nodes import research_node, strategy_node, drafting_node

# 1. Research Graph
def build_research_graph():
    workflow = StateGraph(AgentState)
    workflow.add_node("research", research_node)
    workflow.set_entry_point("research")
    workflow.add_edge("research", END)
    return workflow.compile()

# 2. Strategy Graph
def build_strategy_graph():
    workflow = StateGraph(AgentState)
    workflow.add_node("strategy", strategy_node)
    workflow.set_entry_point("strategy")
    workflow.add_edge("strategy", END)
    return workflow.compile()

# 3. Drafting Graph
def build_drafting_graph():
    workflow = StateGraph(AgentState)
    workflow.add_node("drafting", drafting_node)
    workflow.set_entry_point("drafting")
    workflow.add_edge("drafting", END)
    return workflow.compile()

# Singleton instances
research_app = build_research_graph()
strategy_app = build_strategy_graph()
drafting_app = build_drafting_graph()