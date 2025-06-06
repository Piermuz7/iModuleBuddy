import time
from datetime import date

import streamlit as st
from supabase import Client
from utils.auth import get_supabase
from utils.models import Student

supabase: Client = get_supabase()
user = supabase.auth.get_user().user

def get_student():
    response = supabase.table('student').select('*').eq('id', user.id).execute()
    if len(response.data) == 0:
        return None
    student = Student.from_dict(response.data[0])
    return student

def create_student(student: Student):
    try:
        student.id = user.id
        supabase.table("student").insert(student.to_dict()).execute()
        success = st.success("Student created successfully!")
        time.sleep(3)
        success.empty()
    except Exception as e:
        print(e)
        st.error("Creation failed: " + str(e))

def update_student(student: Student):
    try:
        supabase.table("student").update(student.to_dict()).eq("id", student.id).execute()
        success = st.success("Student updated successfully!")
        time.sleep(3)
        success.empty()
    except Exception as e:
        print(e)
        st.error("Update failed: " + str(e))

def get_work_experience():
    response = supabase.from_('work_experience').select('company_name, occupation, start_date, end_date, current_work, id, part_time').eq('user_id', user.id).order("start_date", desc=True).execute()
    return response.data

def has_work_experience():
    experiences = get_work_experience()
    return experiences is not None and len(experiences) > 0

def add_work_experience(company_name: str, occupation: str, start_date: date, end_date: date, current_work: bool, part_time: bool):
    try:
        we = {
            'company_name': company_name,
            'occupation': occupation,
            'start_date': start_date.strftime('%Y-%m-%d'),
            'end_date': None if current_work else end_date.strftime('%Y-%m-%d'),
            'current_work': current_work,
            'user_id': user.id,
            'part_time': part_time
        }
        supabase.from_('work_experience').insert(we).execute()
        st.rerun()
    except Exception as e:
        print(e)
        st.error("Insertion failed: " + str(e))

def update_work_experience(company_name: str, occupation: str, start_date: date, end_date: date, current_work: bool, we_id: str):
    try:
        we = {
            'company_name': company_name,
            'occupation': occupation,
            'start_date': start_date.strftime('%Y-%m-%d'),
            'end_date': None if current_work else end_date.strftime('%Y-%m-%d'),
            'current_work': current_work,
        }
        supabase.from_('work_experience').update(we).eq('id', we_id).execute()
        st.rerun()
    except Exception as e:
        print(e)
        st.error("Update failed: " + str(e))

def delete_work_experience(we_id: str):
    try:
        supabase.from_('work_experience').delete().eq('id', we_id).execute()
        st.rerun()
    except Exception as e:
        print(e)
        st.error("Deletion failed: " + str(e))