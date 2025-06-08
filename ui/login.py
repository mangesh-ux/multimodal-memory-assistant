import streamlit as st
import os
import json
from pathlib import Path

USER_DB = Path("data/users.json")
USER_DB.parent.mkdir(exist_ok=True)
if not USER_DB.exists():
    USER_DB.write_text("{}", encoding="utf-8")

def load_users():
    with open(USER_DB, "r", encoding="utf-8") as f:
        return json.load(f)

def save_users(users):
    with open(USER_DB, "w", encoding="utf-8") as f:
        json.dump(users, f, indent=2)

def login_screen():
    st.markdown("## 🔐 Login / Sign Up")

    with st.form("auth_form", clear_on_submit=False):
        mode = st.radio("Choose an option:", ["Login", "Sign Up"], horizontal=True)
        username = st.text_input("Username")
        password = st.text_input("Password", type="password")
        submit = st.form_submit_button("🔓 Submit")

    if submit:
        if not username or not password:
            st.warning("Please enter both username and password.")
            return None

        users = load_users()

        if mode == "Login":
            if username not in users:
                st.error("User does not exist. Please sign up first.")
                return None
            if users[username] != password:
                st.error("Incorrect password.")
                return None
            st.session_state.user_id = username
            return username

        else:  # Sign Up
            if username in users:
                st.error("Username already exists. Try logging in instead.")
                return None
            users[username] = password
            save_users(users)
            st.success(f"Account created! Welcome, {username}!")
            st.session_state.user_id = username
            return username

def get_logged_in_user():
    return st.session_state.get("user_id")
