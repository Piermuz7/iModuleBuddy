# pages/login.py
import streamlit as st
from utils.auth import login_user, is_authenticated

# If the user is already authenticated, redirect to the homepage
if is_authenticated():
    st.warning("You are already registered and logged in!")
    st.stop()

# Streamlit form for login
st.title("Login")
email = st.text_input("Email")
password = st.text_input("Password", type="password")

if st.button("Login"):
    user = login_user(email, password)
