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
    if st.session_state.get("is_authenticated"):
        return st.session_state.get("user_id")

    st.title("🔐 Login / Sign Up")

    action = st.radio("Choose an option:", ["Login", "Sign Up"], key="auth_action")
    username = st.text_input("Username", key="auth_username")
    password = st.text_input("Password", type="password", key="auth_password")

    creds = load_credentials()

    if username and password:
        if action == "Login":
            if username in creds["users"]:
                stored_hash = creds["users"][username]["password"]
                if check_password(password, stored_hash):
                    st.session_state.user_id = username
                    st.session_state.is_authenticated = True
                    st.success(f"Welcome back, {username}!")
                    st.rerun()
                else:
                    st.error("Incorrect password.")
            else:
                st.warning("Username not found.")
        elif action == "Sign Up":
            if username in creds["users"]:
                st.warning("Username already exists.")
            else:
                creds["users"][username] = {
                    "email": "",
                    "password": hash_password(password)
                }
                save_credentials(creds)
                st.success("User registered! Please log in.")

    return None
