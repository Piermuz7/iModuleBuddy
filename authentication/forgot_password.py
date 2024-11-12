# pages/forgot_password.py
import streamlit as st
from utils.auth import reset_password, is_authenticated

# If the user is authenticated, prevent accessing the forgot password page
if is_authenticated():
    st.warning("You are already logged in!")
    st.stop()

# Streamlit form for password reset
st.title("Forgot Password")
email = st.text_input("Enter your email to reset password")

if st.button("Reset Password"):
    response = reset_password(email)
    if response:
        st.success("Password reset email sent! Please check your inbox.")
