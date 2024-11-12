import streamlit as st
from utils.auth import logout_user
from utils.supabase_methods import get_student

st.title("Logout")
boh = get_student()
st.write("Hello User: "+boh.name)
st.button("Logout", on_click=logout_user, type="primary")
