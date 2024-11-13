import streamlit as st
from utils.auth import logout_user
from utils.supabase_methods import get_student

st.title("Logout")
st.write("Hello There!")
st.button("Logout", on_click=logout_user, type="primary")
