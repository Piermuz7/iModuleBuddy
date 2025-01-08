import streamlit as st
from assistant.generation_functions.study_plan_by_occupation import create_study_plan_by_occupations

def generate_study_plan(function: callable):
    with st.spinner("Generating study plan... please wait..."):
        message = function()

    st.success("Study plan generated successfully!")
    st.write(message)
st.title("Get a Study Plan")
if st.button("Based on your desired occupations"):
    generate_study_plan(create_study_plan_by_occupations)