from datetime import date

import streamlit as st
import pandas as pd
from utils.neo4j_methods import get_occupations
from utils.supabase_methods import get_work_experience, add_work_experience

st.title("Working Career Details")
work_experiences = get_work_experience()
occupations = get_occupations()

current_occ = st.checkbox("I currently work here")
if current_occ:
    st.success("You are currently working here")
with st.form("my_form", clear_on_submit=True):
    company = st.text_input("Company")
    position = st.selectbox("Position", occupations, placeholder='Choose an option')
    start = st.date_input("Start Date",date.today())
    end = st.date_input("End Date", date.today(), disabled=current_occ, max_value=date.today())
    submitted = st.form_submit_button("Submit")
    if submitted:
        if len(company) < 1 or len(position) < 1:
            st.error("Company and Position are required")

        else:
            add_work_experience(company, position, start, end, current_occ)

# Display the updated work experiences table
st.dataframe(work_experiences,use_container_width=True)