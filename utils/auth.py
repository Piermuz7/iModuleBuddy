import streamlit as st
from supabase import create_client, Client

supabase: Client = create_client(st.secrets['SUPABASE_URL'], st.secrets['SUPABASE_KEY'])

def get_supabase():
    return supabase

def login_user(email: str, password: str):
    try:
        response = supabase.auth.sign_in_with_password({"email": email, "password":password})
        if response.user:
            st.session_state.role = "User"
            st.rerun()
    except Exception as e:
        print(e)
        st.error("Login failed: " + str(e))

def register_user(email: str, password: str):
    try:
        response = supabase.auth.sign_up({"email": email, "password":password})
        return response.user
    except Exception as e:
        print(e)
        st.error("Registration failed: " + str(e))
        return None


def reset_password(email: str):
    response = supabase.auth.api.reset_password_for_email(email)
    if response.get("error"):
        st.error("Error: " + response["error"]["message"])
        return None
    return response

def is_authenticated() -> bool:
    session = supabase.auth.get_session()
    return session is not None

def get_current_user():
    response = supabase.auth.get_user()
    return response.user

def logout_user():
    supabase.auth.sign_out()
    st.session_state.role = None
    st.success("You have logged out successfully")
