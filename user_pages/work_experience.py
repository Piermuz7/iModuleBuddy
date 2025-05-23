from datetime import date
import streamlit as st

from utils.neo4j_methods import Neo4jMethods
from utils.supabase_methods import (
    get_work_experience,
    add_work_experience,
    delete_work_experience,
)

st.title("Working Career Details")
work_experiences = get_work_experience()
neo4j_methods = Neo4jMethods()
occupations = neo4j_methods.get_occupations()
with st.expander("Add Work Experience"):
    current_occ = st.checkbox("I currently work here")
    if current_occ:
        st.success("You are currently working here")
    with st.form("my_form", clear_on_submit=True):
        company = st.text_input("Company")
        position = st.selectbox("Position", occupations, placeholder="Choose an option")
        start = st.date_input(
            "Start Date",
            date.today(),
            max_value=date.today(),
            min_value=date(1980, 1, 1),
        )
        end = st.date_input(
            "End Date",
            date.today(),
            disabled=current_occ,
            max_value=date.today(),
            min_value=date(1980, 1, 1),
        )
        part_time = st.checkbox("Part-Time")
        submitted = st.form_submit_button("Submit")
        if submitted:
            if len(company) < 1 or len(position) < 1:
                st.error("Company and Position are required")
            else:
                add_work_experience(
                    company, position, start, end, current_occ, part_time
                )

for we in work_experiences:
    st.divider()
    with st.container(border=True):
        cols = st.columns(6)
        cols[0].write(we["company_name"])
        cols[1].write(we["occupation"])
        cols[2].write("Part-Time" if we["part_time"] else "Full-Time")
        cols[3].write(we["start_date"])
        cols[4].write(we["end_date"] if not we["current_work"] else "Present")
        if cols[5].button("Delete", key=we["id"]):
            delete_work_experience(we["id"])
