import streamlit as st
from utils.auth import logout_user
from utils.supabase_methods import get_student

student = get_student()

if student:
    st.title(f"Hello, {student.name} {student.surname}!")
    if st.button("Logout", on_click=logout_user, type="primary"):
        st.success("You have been logged out.")
else:
    st.title("You are not logged in.")