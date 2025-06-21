import streamlit as st
import json
from datetime import datetime
from agent_openrouter import create_agent
from strategy_manager import StrategyManager

# Page config
st.set_page_config(
    page_title="Strasia Sales Agent",
    page_icon="🤖",
    layout="wide"
)

# Initialize session state
if 'agent' not in st.session_state:
    with st.spinner("🤖 Initializing sales agent..."):
        st.session_state.agent = create_agent()

if 'messages' not in st.session_state:
    st.session_state.messages = []

if 'session_id' not in st.session_state:
    st.session_state.session_id = datetime.now().strftime("%Y%m%d_%H%M%S")

if 'strategy_manager' not in st.session_state:
    st.session_state.strategy_manager = StrategyManager()

# Set strategy context for agent
current_strategy = st.session_state.strategy_manager.get_current_strategy()
st.session_state.agent.set_strategy_context(current_strategy)

def analyze_conversation_outcome(messages):
    """Analyze if link was shared and consultation requested"""
    link_shared = False
    consultation_requested = False
    
    for message in messages:
        if message["role"] == "assistant":
            content = message["content"].upper()
            if "CALENDLY_LINK" in content or "EMAIL" in content:
                link_shared = True
            if "CONSULTATION" in content or "EXPERTS" in content or "CONSULTANTS" in content:
                consultation_requested = True
    
    return link_shared, consultation_requested

# Sidebar
st.sidebar.title("🤖 Agent Controls")

# Strategy metrics
strategy = st.session_state.strategy_manager.get_current_strategy()
metrics = strategy.get('success_metrics', {})

st.sidebar.metric("Conversations", metrics.get('conversations_completed', 0))
st.sidebar.metric("Conversion Rate", f"{metrics.get('conversion_rate', 0):.1f}%")
st.sidebar.metric("Link Timing", f"Message {strategy.get('timing_strategy', {}).get('link_timing', 4)}")

# View Strategy JSON
if st.sidebar.button("📄 View Strategy JSON"):
    st.session_state.show_json = True

# Clear conversation with analysis
if st.sidebar.button("🗑️ Clear Conversation"):
    # Analyze current conversation before clearing
    if len(st.session_state.messages) > 0:
        link_shared, consultation_requested = analyze_conversation_outcome(st.session_state.messages)
        
        if link_shared or len(st.session_state.messages) >= 6:
            st.session_state.strategy_manager.analyze_conversation_success(
                st.session_state.messages, link_shared, consultation_requested
            )
            st.sidebar.success("✅ Strategy updated!")
    
    st.session_state.messages = []
    st.session_state.agent.clear_memory()
    if hasattr(st.session_state, 'conversation_analyzed'):
        delattr(st.session_state, 'conversation_analyzed')
    st.rerun()

# Test scenarios
with st.sidebar.expander("🧪 Test Scenarios"):
    if st.button("💼 Business Inquiry"):
        test_message = "I'm looking to set up a company in Singapore. What do I need to know?"
        st.session_state.test_message = test_message
        st.rerun()
    
    if st.button("💰 Cost Inquiry"):
        test_message = "How much does it cost to incorporate in Hong Kong and what's the timeline?"
        st.session_state.test_message = test_message
        st.rerun()
    
    if st.button("🏦 Banking Inquiry"):
        test_message = "What banking options are available for US companies?"
        st.session_state.test_message = test_message
        st.rerun()
    
    if st.button("🌍 Multi-jurisdiction"):
        test_message = "I need to compare incorporation options between UK and Singapore for my tech startup"
        st.session_state.test_message = test_message
        st.rerun()

# Main interface
st.title("🤖 Strasia Sales Agent")
st.markdown("**AI-Powered Corporate Services Consultant**")
st.markdown("---")

# Show JSON if requested
if hasattr(st.session_state, 'show_json') and st.session_state.show_json:
    with st.expander("📄 Strategy JSON", expanded=True):
        st.json(current_strategy)
        if st.button("Close JSON"):
            delattr(st.session_state, 'show_json')
            st.rerun()

# Chat interface
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# Input handling
user_input = st.chat_input("Type your message here...")

# Handle test message from sidebar
if hasattr(st.session_state, 'test_message'):
    user_input = st.session_state.test_message
    delattr(st.session_state, 'test_message')

if user_input:
    # Add user message
    timestamp = datetime.now().strftime("%H:%M:%S")
    st.session_state.messages.append({
        "role": "user", 
        "content": user_input,
        "timestamp": timestamp
    })
    
    # Display user message
    with st.chat_message("user"):
        st.markdown(user_input)
    
    # Generate and display assistant response
    with st.chat_message("assistant"):
        with st.spinner("Thinking..."):
            try:
                response = st.session_state.agent.generate_response(user_input)
                st.markdown(response)
                
                # Add assistant response to messages
                st.session_state.messages.append({
                    "role": "assistant",
                    "content": response,
                    "timestamp": datetime.now().strftime("%H:%M:%S")
                })
                
            except Exception as e:
                error_msg = f"Error: {str(e)}"
                st.error(error_msg)
                st.session_state.messages.append({
                    "role": "assistant",
                    "content": error_msg,
                    "timestamp": datetime.now().strftime("%H:%M:%S")
                })

# Auto-analyze when link is shared
if len(st.session_state.messages) > 0:
    link_shared, consultation_requested = analyze_conversation_outcome(st.session_state.messages)
    
    # Auto-analyze when conversation ends (when link is shared)
    if link_shared and not hasattr(st.session_state, 'conversation_analyzed'):
        st.session_state.strategy_manager.analyze_conversation_success(
            st.session_state.messages, link_shared, consultation_requested
        )
        st.session_state.conversation_analyzed = True
        st.success("🧠 AI learned from this conversation!")
