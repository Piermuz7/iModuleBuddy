import streamlit as st
from utils.neo4j_methods import get_modules, get_occupations
from utils.supabase_methods import get_student, update_student, create_student
from utils.models import Student

st.title("Student Career Details")
student = get_student()
new_account = False
if student is None:
    new_account = True
    student = Student.new_student()
courses = get_modules()
occupations = get_occupations()

with st.form("my_form"):
    name = st.text_input("Name", value=student.name)
    surname = st.text_input("Surname", value=student.surname)
    part_time = st.checkbox("I am a Part-Time Student", value=not student.full_time)
    semesters = st.slider("Expected Semesters", 3, 10, value=student.expected_semesters)
    desired_jobs = st.multiselect("Select your career path",
                                  occupations,
                                  placeholder='Choose one or more options',
                                  default=filter(lambda i: i in student.desired_jobs, occupations), )
    taken_courses = st.multiselect("Courses already taken",
                                   courses,
                                   default=filter(lambda i: i in student.taken_courses, courses),
                                   placeholder='Choose one or more options', )
    # to_take_courses = st.multiselect("Courses you'd like to take",
    #                                  filter(lambda i: i not in taken_courses, courses),
    #                                  placeholder='Choose one or more options', )
    submitted = st.form_submit_button("Submit")
    if submitted:
        new_s = Student(desired_jobs, not part_time, student.id, name, surname, semesters, taken_courses)
        data = create_student(new_s) if new_account else update_student(new_s)
        if data is not None:
            new_account = False
