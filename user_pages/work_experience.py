from datetime import date

import streamlit as st
import pandas as pd
from utils.neo4j_methods import get_occupations
from utils.supabase_methods import get_work_experience, add_work_experience

def save_work_experience(company, position, start, end):
    if len(company)<1 or len(position)<1:
        st.error("Company and Position are required")
        return
    # Load existing work experiences from a file or database
    work_experiences = pd.read_csv('work.csv')
    
    # Create a new row with the work experience details

    new_row = {'Company': company, 'Position': position, 'StartDate': start, 'EndDate': end}
    
    # Add the new row to the work experiences table
    work_experiences = pd.concat([work_experiences,pd.DataFrame(new_row, index=[0])])
    
    # Save the updated work experiences table back to the file or database
    work_experiences.to_csv('work.csv', index=False)
    st.success("Work experience saved successfully!")


st.title("Working Career Details")
work_experiences = get_work_experience()
occupations = get_occupations()
    # Get user input
ended = st.checkbox("I currently work here")
if ended:
    st.success("You are currently working here")
with st.form("my_form", clear_on_submit=True):
    company = st.text_input("Company")
    position = st.selectbox("Position", occupations, placeholder='Choose an option')
    start = st.date_input("Start Date",date.today())
    end = st.date_input("End Date", date.today(), disabled=ended, max_value=date.today())
    submitted = st.form_submit_button("Submit")
    if submitted:
        if len(company) < 1 or len(position) < 1:
            st.error("Company and Position are required")

        else:
            add_work_experience(company, position, start, end, ended)
    
    # Display the updated work experiences table
st.dataframe(work_experiences,use_container_width=True)