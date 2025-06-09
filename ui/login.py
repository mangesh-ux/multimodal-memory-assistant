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

def attempt_auth(mode, username, password):
    if not username or not password:
        st.session_state.auth_error = "Please enter both username and password."
        return

    users = load_users()

    if mode == "Login to your MemoBrain account":
        if username not in users:
            st.session_state.auth_error = "User does not exist. Please sign up first."
            return
        if users[username] != password:
            st.session_state.auth_error = "Incorrect password."
            return
        st.session_state.user_id = username
    else:  # Sign Up
        if username in users:
            st.session_state.auth_error = "Username already exists. Try logging in instead."
            return
        users[username] = password
        save_users(users)
        st.session_state.user_id = username

def login_screen():
    st.markdown("## 🔐 Login / Sign Up")

    if "auth_error" in st.session_state:
        st.error(st.session_state.auth_error)

    if "auth_mode" not in st.session_state:
        st.session_state.auth_mode = "Login"

    st.radio(
        "Choose an option:",
        ["Login to your MemoBrain account", "Create a MemoBrain account"],
        index=0 if st.session_state.auth_mode == "Login" else 1,
        horizontal=True,
        key="auth_mode"
    )

    username = st.text_input("Username", key="auth_username")
    password = st.text_input("Password", type="password", key="auth_password")

    st.button(
        "🔓 Submit",
        on_click=attempt_auth,
        args=(st.session_state.auth_mode, username, password)
    )

def get_logged_in_user():
    return st.session_state.get("user_id")
