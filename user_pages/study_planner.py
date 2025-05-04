import asyncio
import streamlit as st
from assistant.agent_workflow import execute_agent_workflow

st.title("Get a Study Plan")

# Track current output and spinner control
if "study_plan_output" not in st.session_state:
    st.session_state.study_plan_output = ""
if "should_generate" not in st.session_state:
    st.session_state.should_generate = False
if "retrieval_strategy" not in st.session_state:
    st.session_state.retrieval_strategy = ""
if "user_msg" not in st.session_state:
    st.session_state.user_msg = ""

# Define columns for button row
col1, col2, col3, col4 = st.columns(4)

with col1:
    if st.button("Past Experience"):
        st.session_state.retrieval_strategy = "past_experience"
        st.session_state.user_msg = "Suggest me some modules based on my past work experiences."
        st.session_state.should_generate = True

with col2:
    if st.button("Future Goals"):
        st.session_state.retrieval_strategy = "future_goals"
        st.session_state.user_msg = "Suggest me some modules based on my future work goals."
        st.session_state.should_generate = True

with col3:
    if st.button("Preferences"):
        st.session_state.retrieval_strategy = "preferences"
        st.session_state.user_msg = "Suggest me some modules based on my preferences."
        st.session_state.should_generate = True

with col4:
    if st.button("Balanced"):
        st.session_state.retrieval_strategy = "balanced"
        st.session_state.user_msg = "Suggest me some modules based on a balanced approach of past work, future goals, and preferences."
        st.session_state.should_generate = True

# If a button was clicked, show spinner and generate plan
if st.session_state.should_generate:
    with st.spinner("Generating study plan... please wait..."):
        content = asyncio.run(
            execute_agent_workflow(
                user_msg=st.session_state.user_msg,
                retrieval_strategy=st.session_state.retrieval_strategy,
            )
        )
    st.session_state.study_plan_output = content
    st.session_state.should_generate = False

# Display result in one panel below all buttons
if st.session_state.study_plan_output:
    st.markdown("---")
    st.success("Study plan generated successfully!")
    st.write(st.session_state.study_plan_output)