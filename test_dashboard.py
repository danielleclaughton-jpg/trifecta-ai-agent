"""
Trifecta AI Agent - Test Dashboard
Streamlit-based testing interface for MCP server and agent validation
Version: 1.0.0 | Created: 2026-01-27
"""

import streamlit as st
import requests
import json
import os
from datetime import datetime

# Page configuration
st.set_page_config(
    page_title="Trifecta AI Agent - Test Dashboard",
    page_icon="🏥",
    layout="wide"
)

# =============================================================================
# CONFIGURATION
# =============================================================================

# Default URLs - can be overridden via environment or sidebar
DEFAULT_MCP_URL = "http://127.0.0.1:3000"
DEFAULT_FLASK_URL = "http://127.0.0.1:5000"

# =============================================================================
# SIDEBAR - CONFIGURATION
# =============================================================================

st.sidebar.title("⚙️ Configuration")

# API URLs
st.sidebar.header("API Endpoints")
mcp_url = st.sidebar.text_input("MCP Server URL", value=os.environ.get("MCP_URL", DEFAULT_MCP_URL))
flask_url = st.sidebar.text_input("Flask API URL", value=os.environ.get("FLASK_URL", DEFAULT_FLASK_URL))

# Connection status
st.sidebar.header("Connection Status")

def check_flask_health():
    """Check Flask API health."""
    try:
        resp = requests.get(f"{flask_url}/health", timeout=5)
        return resp.status_code == 200, resp.json() if resp.status_code == 200 else {"error": resp.text}
    except Exception as e:
        return False, {"error": str(e)}

def check_mcp_health():
    """Check MCP server health."""
    try:
        resp = requests.get(f"{mcp_url}/health", timeout=5)
        return resp.status_code == 200, resp.json() if resp.status_code == 200 else {"error": resp.text}
    except Exception as e:
        return False, {"error": str(e)}

# Check and display status
flask_ok, flask_status = check_flask_health()
mcp_ok, mcp_status = check_mcp_health()

flask_indicator = "🟢 Online" if flask_ok else "🔴 Offline"
st.sidebar.text(f"Flask API: {flask_indicator}")

mcp_indicator = "🟢 Online" if mcp_ok else "🔴 Offline"
st.sidebar.text(f"MCP Server: {mcp_indicator}")

# API Keys status
st.sidebar.header("API Keys Status")
anthropic_status = "✅ Configured" if os.environ.get("ANTHROPIC_API_KEY") else "❌ Missing"
st.sidebar.text(f"Anthropic Claude: {anthropic_status}")

# =============================================================================
# MAIN CONTENT
# =============================================================================

st.title("🏥 Trifecta Recovery Services - AI Agent Test Dashboard")
st.markdown("**Testing Interface for MCP Server and Trifecta AI Agent Integration**")
st.markdown("---")

# =============================================================================
# TABS
# =============================================================================

tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "📊 System Status",
    "💬 Agent Chat",
    "👥 Lead Management",
    "📋 MCP Tools",
    "🔧 Debug"
])

# =============================================================================
# TAB 1: SYSTEM STATUS
# =============================================================================

with tab1:
    st.header("System Health Overview")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Flask API", "Online" if flask_ok else "Offline", delta="Healthy" if flask_ok else "Error")
    with col2:
        st.metric("MCP Server", "Online" if mcp_ok else "Offline", delta="Ready" if mcp_okelse "Not Ready")
    with col3:
        anthropic_ok = bool(os.environ.get("ANTHROPIC_API_KEY"))
        st.metric("Anthropic Claude", "Connected" if anthropic_ok else "Missing Key", delta="Active" if anthropic_ok else "Blocked")
    with col4:
        st.metric("Dashboard", "Running", delta="v1.0.0")
    
    st.subheader("Detailed Status")
    
    if flask_ok:
        st.json(flask_status)
    else:
        st.error(f"Flask API Error: {flask_status.get('error', 'Unknown error')}")
    
    if mcp_ok:
        st.json(mcp_status)
    else:
        st.warning("MCP Server not accessible - ensure server is running on port 3000")

# =============================================================================
# TAB 2: AGENT CHAT
# =============================================================================

with tab2:
    st.header("Trifecta AI Agent Chat Test")
    
    # System prompt context
    with st.expander("System Context", expanded=False):
        system_context = st.text_area(
            "System Prompt",
            value="You are the Trifecta AI Agent for Trifecta Addiction and Mental Health Services. "
                  "You help with lead intake, client management, scheduling, and providing information "
                  "about addiction recovery programs including the 28-Day Virtual Boot Camp, Inpatient Programs, "
                  "and Virtual Outpatient Programs.",
            height=100
        )
    
    # Chat input
    user_message = st.text_area("Your Message", placeholder="Ask about programs, pricing, or help with a client...", height=100)
    
    if st.button("Send to Agent", type="primary"):
        if not user_message.strip():
            st.warning("Please enter a message")
        elif not flask_ok:
            st.error("Flask API is not available")
        else:
            with st.spinner("Agent is thinking..."):
                try:
                    resp = requests.post(
                        f"{flask_url}/api/chat",
                        json={"message": user_message},
                        timeout=30
                    )
                    
                    if resp.status_code == 200:
                        data = resp.json()
                        st.success("Response received!")
                        
                        st.subheader("Agent Response")
                        st.write(data.get("reply", "No response"))
                        
                        if data.get("matched_skill"):
                            st.info(f"Matched Skill: {data.get('skill_title', data.get('matched_skill'))}")
                        
                        st.caption(f"Timestamp: {data.get('timestamp', 'N/A')}")
                    else:
                        st.error(f"Error: {resp.status_code} - {resp.text}")
                except Exception as e:
                    st.error(f"Request failed: {str(e)}")
    
    # Quick prompts
    st.subheader("Quick Prompts")
    quick_prompts = [
        "What programs do you offer?",
        "Tell me about the 28-Day Boot Camp",
        "How can I schedule a consultation?",
        "What is the pricing for inpatient programs?"
    ]
    
    cols = st.columns(2)
    for i, prompt in enumerate(quick_prompts):
        if cols[i % 2].button(prompt, key=f"quick_{i}"):
            st.session_state.quick_message = prompt

# =============================================================================
# TAB 3: LEAD MANAGEMENT
# =============================================================================

with tab3:
    st.header("Lead Management Tools")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Create Lead")
        with st.form("lead_form"):
            name = st.text_input("Lead Name")
            source = st.selectbox("Source", ["Chat - GoDaddy", "Contact Form", "Phone", "Referral", "Website"])
            email = st.text_input("Email")
            phone = st.text_input("Phone")
            program_interest = st.selectbox("Program Interest", ["", "bootcamp", "inpatient", "virtual"])
            initial_question = st.text_area("Initial Question")
            
            submitted = st.form_submit_button("Create Lead", type="primary")
            
            if submitted:
                if not name:
                    st.error("Name is required")
                elif not flask_ok:
                    st.error("Flask API not available")
                else:
                    try:
                        resp = requests.post(
                            f"{flask_url}/api/leads",
                            json={
                                "name": name,
                                "source": source,
                                "email": email,
                                "phone": phone,
                                "program_interest": program_interest,
                                "initial_question": initial_question
                            },
                            timeout=10
                        )
                        if resp.status_code in [200, 201]:
                            st.success(f"Lead created! ID: {resp.json().get('id', 'N/A')}")
                        else:
                            st.error(f"Failed: {resp.status_code}")
                    except Exception as e:
                        st.error(f"Error: {str(e)}")
    
    with col2:
        st.subheader("Lead Scoring")
        with st.form("score_form"):
            lead_name = st.text_input("Lead Name")
            has_email = st.checkbox("Has Email")
            has_phone = st.checkbox("Has Phone")
            asked_pricing = st.checkbox("Asked About Pricing")
            mentioned_urgency = st.checkbox("Mentioned Urgency")
            is_self_referral = st.checkbox("Self-Referral")
            
            scored = st.form_submit_button("Calculate Score")
            
            if scored and lead_name:
                score = 0
                factors = []
                
                if has_email:
                    score += 20
                    factors.append("+20: Has email")
                if has_phone:
                    score += 10
                    factors.append("+10: Has phone")
                if asked_pricing:
                    score += 25
                    factors.append("+25: Asked pricing (high intent)")
                if mentioned_urgency:
                    score += 20
                    factors.append("+20: Mentioned urgency")
                if is_self_referral:
                    score += 15
                    factors.append("+15: Self-referral")
                
                if score >= 70:
                    priority = "🔥 HOT - Contact within 1 hour"
                elif score >= 50:
                    priority = "⭐ WARM - Contact within 4 hours"
                elif score >= 30:
                    priority = "💧 COOL - Contact within 24 hours"
                else:
                    priority = "❄️ COLD - Add to nurture sequence"
                
                st.success(f"Score: {score}/100")
                st.info(f"Priority: {priority}")
                st.write("Factors:", ", ".join(factors))

# =============================================================================
# TAB 4: MCP TOOLS
# =============================================================================

with tab4:
    st.header("MCP Server Tools Test")
    
    tool_category = st.selectbox("Tool Category", [
        "API Integration",
        "Lead Management",
        "Communications",
        "Crisis Detection",
        "Client Management",
        "Sessions",
        "Scheduling",
        "Analytics",
        "Workflow"
    ])
    
    st.subheader(f"{tool_category} Tools")
    
    if tool_category == "API Integration":
        if st.button("check_api_health"):
            if mcp_ok:
                st.json(mcp_status)
            else:
                st.error("MCP server not available")
    
    elif tool_category == "Lead Management":
        col1, col2 = st.columns(2)
        with col1:
            if st.button("create_lead"):
                st.info("Use Lead Management tab for full form")
        with col2:
            if st.button("score_lead"):
                st.info("Use Lead Management tab for scoring")
    
    elif tool_category == "Communications":
        st.subheader("Generate Chat Response")
        with st.form("chat_response"):
            lead_name = st.text_input("Lead Name", value="there")
            inquiry_type = st.selectbox("Inquiry Type", ["general", "pricing", "program", "professional"])
            specific_question = st.text_area("Specific Question")
            
            if st.button("Generate Response"):
                st.info("Response would be generated via MCP tool call")
    
    elif tool_category == "Crisis Detection":
        st.subheader("Crisis Risk Analysis")
        with st.form("crisis_analysis"):
            text = st.text_area("Text to Analyze", placeholder="Enter message text to analyze for crisis indicators...")
            context = st.selectbox("Context", ["message", "call", "session_note"])
            
            if st.button("Analyze Crisis Risk"):
                st.info("Would call analyze_crisis_risk MCP tool")
    
    elif tool_category == "Analytics":
        if st.button("get_dashboard_metrics"):
            if flask_ok:
                try:
                    resp =requests.get(f"{flask_url}/api/dashboard/metrics", timeout=5)
                    st.json(resp.json())
                except Exception as e:
                    st.error(f"Error: {str(e)}")
            else:
                st.error("Flask API not available")
    
    elif tool_category == "Workflow":
        if st.button("get_daily_checklist"):
            st.info("Would return daily workflow checklist")

# =============================================================================
# TAB 5: DEBUG
# =============================================================================

with tab5:
    st.header("Debug Information")
    
    st.subheader("Environment Variables")
    env_vars = {
        "MCP_URL": os.environ.get("MCP_URL", "Not set"),
        "FLASK_URL": os.environ.get("FLASK_URL", "Not set"),
        "ANTHROPIC_API_KEY": "***set***" if os.environ.get("ANTHROPIC_API_KEY") else "Not set",
    }
    st.json(env_vars)
    
    st.subheader("Test API Direct Calls")
    
    if st.button("Test Flask /health"):
        try:
            resp = requests.get(f"{flask_url}/health", timeout=5)
            st.json(resp.json())
        except Exception as e:
            st.error(f"Failed: {str(e)}")
    
    if st.button("Test Flask /api/skills"):
        try:
            resp = requests.get(f"{flask_url}/api/skills", timeout=5)
            st.json(resp.json())
        except Exception as e:
            st.error(f"Failed: {str(e)}")
    
    if st.button("Test MCP /health"):
        try:
            resp = requests.get(f"{mcp_url}/health", timeout=5)
            st.json(resp.json())
        except Exception as e:
            st.error(f"Failed: {str(e)}")
    
    st.subheader("Logs")
    log_area = st.text_area("Activity Log", height=200, placeholder="Activity will appear here...")
    
    if st.button("Clear Log"):
        st.session_state.log = ""

# =============================================================================
# FOOTER
# =============================================================================

st.markdown("---")
st.caption(f"Trifecta AI Agent Test Dashboard | Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
st.caption("For testing only - Not for production use")
