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
    st.markdown("<h2 style='text-align: center;'>🧠 Welcome to MemoBrain</h2>", unsafe_allow_html=True)
    
    # Create columns for centering the login form
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:
        st.markdown("<div style='background-color: #f8f9fa; padding: 20px; border-radius: 10px; box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);'>", unsafe_allow_html=True)
        
        if "auth_error" in st.session_state:
            st.error(st.session_state.auth_error)

        if "auth_mode" not in st.session_state:
            st.session_state.auth_mode = "Login to your MemoBrain account"

        st.radio(
            "Choose an option:",
            ["Login to your MemoBrain account", "Create a MemoBrain account"],
            index=0 if st.session_state.auth_mode == "Login to your MemoBrain account" else 1,
            horizontal=True,
            key="auth_mode"
        )

        username = st.text_input("Username", key="auth_username")
        password = st.text_input("Password", type="password", key="auth_password")

        col_btn1, col_btn2 = st.columns([1, 1])
        with col_btn1:
            if st.session_state.auth_mode == "Login to your MemoBrain account":
                btn_label = "🔓 Login"
            else:
                btn_label = "✨ Sign Up"
                
            st.button(
                btn_label,
                on_click=attempt_auth,
                args=(st.session_state.auth_mode, username, password),
                use_container_width=True
            )
        
        with col_btn2:
            st.button("🧪 Demo Mode", on_click=enter_demo_mode, use_container_width=True)
            
        st.markdown("</div>", unsafe_allow_html=True)
        
        # Add helpful information
        with st.expander("Need help?"):
            st.markdown("**Forgot password?** Please contact support.")
            st.markdown("**First time user?** Select 'Create a MemoBrain account' to get started.")

def get_logged_in_user():
    return st.session_state.get("user_id")
