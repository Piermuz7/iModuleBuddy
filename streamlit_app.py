import streamlit as st
from utils.auth import is_authenticated

is_auth = is_authenticated()
logout_page = st.Page(
    "authentication/logout.py",
    title="Log out",
    default=is_auth,
)
login = st.Page(
    "authentication/login.py",
    title="Login",
    default=(not is_auth),
)
register = st.Page(
    "authentication/register.py",
    title="Register",
)
student_career = st.Page(
    "user_pages/student_career.py",
    title="Student Career",
)
work_experience = st.Page(
    "user_pages/work_experience.py",
    title="Work Experience",
)
study_planner = st.Page(
    "user_pages/study_planner.py",
    title="Study Planner",
)
account_pages = [logout_page]
student_pages = [student_career, work_experience, study_planner]
not_auth_pages = [login, register]
if is_authenticated():
    pg = st.navigation(
        {"Account": account_pages} | {"Student Prefences and Career": student_pages}
    )
else:
    pg = st.navigation({"Authentication": not_auth_pages})

pg.run()
