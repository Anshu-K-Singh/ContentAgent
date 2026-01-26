import streamlit as st
import requests
import time
import json

# --- CONFIG ---
# API_URL = "http://localhost:8000/agent"
API_URL = "https://contentagent.onrender.com/agent"
st.set_page_config(page_title="ContentForge Agent", page_icon="🤖", layout="wide")

# --- SESSION STATE ---
if "workflow_id" not in st.session_state:
    st.session_state.workflow_id = None
if "current_status" not in st.session_state:
    st.session_state.current_status = None

# --- SIDEBAR ---
with st.sidebar:
    st.header("🤖 ContentForge")
    st.markdown("Your Autonomous AI Editorial Team.")
    if st.button("Reset / New Post", type="primary"):
        st.session_state.workflow_id = None
        st.session_state.current_status = None
        st.rerun()

    st.divider()
    if st.session_state.workflow_id:
        st.caption(f"Workflow ID:\n`{st.session_state.workflow_id}`")
        st.info(f"Status: {st.session_state.current_status}")

# --- API FUNCTIONS ---
def start_agent(topic):
    try:
        res = requests.post(f"{API_URL}/start", json={"topic": topic})  # Changed to JSON body
        if res.status_code == 200:
            return res.json()
    except Exception as e:
        st.error(f"Failed to connect to backend: {e}")
    return None

def get_status(workflow_id):
    try:
        res = requests.get(f"{API_URL}/{workflow_id}")
        if res.status_code == 200:
            return res.json()
    except:
        return None

def send_approval(workflow_id, feedback=None):
    payload = {"user_feedback": feedback} if feedback else {}  # JSON body
    requests.post(f"{API_URL}/{workflow_id}/approve-research", json=payload)

def send_selection(workflow_id, strategy_id):
    requests.post(f"{API_URL}/{workflow_id}/select-strategy", params={"strategy_id": int(strategy_id)})  # Convert to str

# --- MAIN UI LOGIC ---

st.title("🚀 Autonomous Content Agent")

# PHASE 1: START
if not st.session_state.workflow_id:
    st.markdown("Enter a topic, and I'll research, strategize, and write high-viral content for you.")
    topic = st.text_input("What do you want to post about?", placeholder="e.g., The Future of AI Agents")
    
    if st.button("Start Workflow"):
        if topic:
            with st.spinner("Initializing Agent..."):
                data = start_agent(topic)
                if data:
                    st.session_state.workflow_id = data["id"]
                    st.session_state.current_status = data["status"]
                    st.rerun()

# PHASE 2: POLLING & STATE MANAGEMENT
else:
    # Poll backend for latest status
    workflow_data = get_status(st.session_state.workflow_id)
    
    if not workflow_data:
        st.error("Could not fetch workflow data.")
        st.stop()
        
    status = workflow_data["status"]
    st.session_state.current_status = status

    # ---------------------------------------------------------
    # STATE: RESEARCHING
    # ---------------------------------------------------------
    if status == "researching":
        st.status("🕵️ Agent is browsing the web...", expanded=True)
        time.sleep(3) # Polling interval
        st.rerun()

    # ---------------------------------------------------------
    # STATE: RESEARCH APPROVAL (HUMAN IN LOOP 1)
    # ---------------------------------------------------------
    elif status == "waiting_research_approval":
        st.success("✅ Research Complete!")
        
        with st.expander("📄 Review Research Brief", expanded=True):
            data = workflow_data.get("research_data", {})
            
            # Show key points prominently
            st.markdown("### 🔑 Key Takeaways")
            for point in data.get("key_points", []):
                st.markdown(f"- {point}")
            
            st.divider()
            
            # Show full summary
            summary_text = st.text_area(
                "Research Summary (You can edit this):", 
                value=data.get("summary", ""),
                height=300
            )
            
            st.markdown("**Sources:**")
            for src in data.get("sources", []):
                st.markdown(f"- {src}")
            
            if st.button("Approve & Strategize"):
                send_approval(st.session_state.workflow_id, feedback=summary_text)
                st.rerun()

    # ---------------------------------------------------------
    # STATE: STRATEGIZING
    # ---------------------------------------------------------
    elif status == "strategizing":
        st.status("♟️ Agent is brainstorming angles...", expanded=True)
        time.sleep(3)
        st.rerun()

    # ---------------------------------------------------------
    # STATE: STRATEGY SELECTION (HUMAN IN LOOP 2)
    # ---------------------------------------------------------
    elif status == "waiting_strategy_selection":
        st.success("✅ Strategy Options Ready!")
        st.markdown("### Choose a Content Direction:")
        
        strategies = workflow_data.get("strategies", [])
        
        cols = st.columns(len(strategies))
        
        for idx, strategy in enumerate(strategies):
            with cols[idx]:
                st.info(f"**Angle {idx+1}: {strategy['angle']}**")
                st.caption(strategy["hook"])
                st.markdown(f"*{strategy['description']}*")
                
                if st.button(f"Select Option {idx+1}", key=f"btn_{strategy['id']}"):
                    send_selection(st.session_state.workflow_id, strategy["id"])
                    st.rerun()

    # ---------------------------------------------------------
    # STATE: DRAFTING
    # ---------------------------------------------------------
    elif status == "drafting":
        st.status("✍️ Agent is writing & designing...", expanded=True)
        time.sleep(3)
        st.rerun()

    # ---------------------------------------------------------
    # STATE: COMPLETED
    # ---------------------------------------------------------
    elif status == "completed":
        st.balloons()
        st.success("✨ Content Generated Successfully!")
        
        final = workflow_data.get("final_content", {})
        
        # Two columns: Image vs Text
        col_img, col_txt = st.columns([1, 2])
        
        with col_img:
            st.image(final.get("image_url"), caption="AI Generated Visual")
            st.markdown(f"**Prompt:** `{final.get('image_prompt')}`")
        
        with col_txt:
            tab1, tab2 = st.tabs(["LinkedIn Post", "Twitter Thread"])
            
            with tab1:
                st.text_area("Copy for LinkedIn:", value=final.get("linkedin_post"), height=400)
            
            with tab2:
                thread = final.get("twitter_thread", [])
                for i, tweet in enumerate(thread):
                    st.text_area(f"Tweet {i+1}", value=tweet, height=100)