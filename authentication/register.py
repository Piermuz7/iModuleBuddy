# pages/register.py
import streamlit as st
from utils.auth import register_user, is_authenticated

# If the user is already authenticated, redirect to the homepage
if is_authenticated():
    st.warning("You are already registered and logged in!")
    st.stop()

# Streamlit form for registration
st.title("Register")
email = st.text_input("Email")
password = st.text_input("Password", type="password")

if st.button("Register"):
    user = register_user(email, password)
    if user:
        st.session_state["logged_in"] = True
        st.success("Registration successful! Confirm your email before logging in. Check your inbox.")
        st.rerun()
