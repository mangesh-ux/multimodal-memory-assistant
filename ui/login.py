# ui/login.py

import streamlit as st
import bcrypt
import json
from pathlib import Path

CREDENTIALS_PATH = Path("data/credentials.json")

def load_credentials():
    if CREDENTIALS_PATH.exists():
        with open(CREDENTIALS_PATH, "r") as f:
            return json.load(f)
    else:
        return {"users": {}}

def save_credentials(data):
    with open(CREDENTIALS_PATH, "w") as f:
        json.dump(data, f, indent=2)

def hash_password(password):
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()

def check_password(password, hashed):
    return bcrypt.checkpw(password.encode(), hashed.encode())

def login_signup_ui():
    st.sidebar.title("🔐 Login / Sign Up")

    action = st.sidebar.radio("Choose an option:", ["Login", "Sign Up"], key="auth_action")

    username = st.sidebar.text_input("Username", key="auth_username")
    password = st.sidebar.text_input("Password", type="password", key="auth_password")

    if not username or not password:
        return None

    creds = load_credentials()

    if action == "Login":
        if username in creds["users"]:
            stored_hash = creds["users"][username]["password"]
            if check_password(password, stored_hash):
                st.session_state.user_id = username
                st.sidebar.success(f"Welcome back, {username}!")
            else:
                st.sidebar.error("Incorrect password.")
        else:
            st.sidebar.warning("Username not found.")
    elif action == "Sign Up":
        if username in creds["users"]:
            st.sidebar.warning("Username already exists.")
        else:
            hashed = hash_password(password)
            creds["users"][username] = {
                "email": "",
                "password": hashed
            }
            save_credentials(creds)
            st.sidebar.success("User registered. Please login.")

    return st.session_state.get("user_id", None)
