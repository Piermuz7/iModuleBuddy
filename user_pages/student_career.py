import time
import streamlit as st
import pandas as pd
from utils.neo4j_methods import get_modules, get_occupations
from utils.supabase_methods import get_student, update_student
from utils.models import Student

st.title("Student Career Details")
student = get_student()
courses = get_modules()
occupations = get_occupations()

with st.form("my_form"):
    full_time = st.checkbox("I am a Full-Time Student",value=student.full_time)
    desired_jobs = st.multiselect("Select your career path",
               occupations,
               placeholder='Choose one or more options',
               default=filter(lambda i: i in student.desired_jobs, occupations),)

    taken_courses = st.multiselect("Courses already taken",
                                   courses,
                                   default=filter(lambda i: i in student.taken_courses, courses),
                                   placeholder='Choose one or more options', )
    # to_take_courses = st.multiselect("Courses you'd like to take",
    #                                  filter(lambda i: i not in taken_courses, courses),
    #                                  placeholder='Choose one or more options', )
    submitted = st.form_submit_button("Submit")
    if submitted:
        updated_student = Student(desired_jobs, full_time, student.id, student.name, student.surname, taken_courses)
        data = update_student(updated_student)
