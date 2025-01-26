import asyncio
import streamlit as st

from assistant.agent_workflow import execute_agent_workflow


def generate_study_plan(function: callable):
    with st.spinner("Generating study plan... please wait..."):
        message = function()

    st.success("Study plan generated successfully!")
    st.write(message)


st.title("Get a Study Plan")
if st.button("Generate Study Plan for Desired Occupations"):
    with st.spinner("Generating study plan... please wait..."):
        content = asyncio.run(
            execute_agent_workflow(
                user_msg="Suggest me some modules based on my desired occupations and then create a study plan based on the suggested modules."
            )
        )
    st.success("Study plan generated successfully!")
    st.write(content)
