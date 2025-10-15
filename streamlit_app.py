# streamlit_app.py
import streamlit as st
import asyncio
from main import weather_Agent, config, session
from agents import Runner

# Page config
st.set_page_config(
    page_title="Weather Agent",
    page_icon="🪶",
    layout="centered",
    initial_sidebar_state="collapsed"
)

# App Header
st.title("Weather Agent")
st.markdown("""
<style>
    body {
        background-color: #f9f9f9;
    }
    .stTextInput textarea {
        border: 2px solid #00b4d8;
        border-radius: 10px;
    }
    .stButton>button {
        background-color: #00b4d8;
        color: white;
        font-weight: bold;
        border-radius: 10px;
    }
</style>
""", unsafe_allow_html=True)

st.markdown("**🌤️ Bilingual Smart Weather Companion (English + Urdu)**")
st.caption("Powered by Agentic AI with input/output guardrails 💡")

# Text input area
user_input = st.text_area(
    "Enter your request:",
    placeholder="e.g. Give me the current weather of Karachi...",
    height=150
)

# Chat memory area (optional)
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

# Generate button
if st.button("✨ Get Weather"):
    if not user_input.strip():
        st.warning("Please enter something first.")
    else:
        with st.spinner("Getting Weather Update... 🎭"):
            async def get_update():
                result = await Runner.run(
                    weather_Agent,
                    input=user_input,
                    run_config=config,
                    session=session
                )
                return result.final_output or "Sorry, I'm unable to fetch that."

            weather_output = asyncio.run(get_update())

        st.session_state.chat_history.append(
            {"user": user_input, "agent": weather_output}
        )

# Display chat history
if st.session_state.chat_history:
    for i, chat in enumerate(st.session_state.chat_history[::-1]):
        with st.expander(f"🧍 You: {chat['user'][:30]}..."):
            st.markdown(f"**🧍 You:** {chat['user']}")
            st.markdown(f"**🤖 Agent:**\n{chat['agent']}")
 