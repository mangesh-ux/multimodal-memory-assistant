import streamlit as st
import os
import json
import time
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
        
        # Create user directory
        from core.user_paths import get_user_data_dir
        user_dir = get_user_data_dir(username)
        # Path(user_dir).mkdir(parents=True, exist_ok=True)  # This line is unnecessary as get_user_data_dir already creates the directory

def enter_demo_mode():
    """Enter a demo mode with a temporary user account"""
    # Generate a unique demo username
    demo_username = f"demo_user_{os.urandom(4).hex()}"
    demo_password = os.urandom(8).hex()
    
    # Create a temporary user
    users = load_users()
    users[demo_username] = demo_password
    save_users(users)
    
    # Set session state
    st.session_state.user_id = demo_username
    st.session_state.is_demo = True
    st.session_state.demo_expiry = time.time() + (60 * 60)  # 1 hour demo
    
    # Create demo user directory
    from core.user_paths import get_user_data_dir
    user_dir = get_user_data_dir(demo_username)
    # Path(user_dir).mkdir(parents=True, exist_ok=True)  # This line is unnecessary as get_user_data_dir already creates the directory

def check_demo_expiry():
    """Check if the demo mode has expired"""
    if st.session_state.get("is_demo") and st.session_state.get("demo_expiry"):
        current_time = time.time()
        if current_time > st.session_state.demo_expiry:
            # Demo has expired, log the user out
            st.session_state.pop("user_id", None)
            st.session_state.pop("is_demo", None)
            st.session_state.pop("demo_expiry", None)
            st.session_state.demo_expired = True
            return True
    return False

def show_demo_banner():
    """Show a banner when in demo mode"""
    if st.session_state.get("is_demo"):
        # Calculate remaining time
        current_time = time.time()
        expiry_time = st.session_state.demo_expiry
        remaining_minutes = max(0, int((expiry_time - current_time) / 60))
        
        # Display banner
        st.warning(
            f"🧪 **Demo Mode** - Your session will expire in {remaining_minutes} minutes. "
            f"[Create an account](/) to save your data permanently."
        )
    
    # Show message if demo just expired
    if st.session_state.get("demo_expired"):
        st.error("Your demo session has expired. Please log in or create a new account.")
        # Clear the flag after showing the message
        st.session_state.pop("demo_expired", None)

def cleanup_expired_demos():
    """Clean up expired demo accounts"""
    import shutil
    from core.user_paths import get_user_data_dir
    from core.delete_memory import delete_user_memory
    
    # Find demo users
    users = load_users()
    demo_users = [user for user in users.keys() if user.startswith("demo_user_")]
    
    # Check each demo user
    for demo_user in demo_users:
        # For a real implementation, you would store expiry times in a database
        # Here we'll just remove demo accounts older than 24 hours based on file timestamps
        user_dir = Path(get_user_data_dir(demo_user))
        if user_dir.exists():
            # Check creation time of directory
            import os
            creation_time = os.path.getctime(user_dir)
            if time.time() - creation_time > 24 * 60 * 60:  # 24 hours
                # Delete user data
                delete_user_memory(demo_user)
                # Remove from users database
                if demo_user in users:
                    del users[demo_user]
                    save_users(users)

def login_screen():
    # Add MemoBrain logo and tagline
    st.markdown('<div style="display:flex; flex-direction:column; align-items:center; margin-bottom:1.5rem;">', unsafe_allow_html=True)
    st.image("./screenshots/logo_image.png", width=180)
    st.markdown('<div style="color:#a0a0a0; font-size:1.1rem; text-align:center; margin-top:0.5rem;">Your Personal Memory Operating System</div>', unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)
    st.markdown("## 🔐 Login / Sign Up")

    if "auth_error" in st.session_state:
        st.error(st.session_state.auth_error)

    if "auth_mode" not in st.session_state:
        st.session_state.auth_mode = "Login to your MemoBrain account"

    # Create columns for a better layout
    col1, col2 = st.columns([3, 1])
    
    with col1:
        st.radio(
            "Choose an option:",
            ["Login to your MemoBrain account", "Create a MemoBrain account"],
            index=0 if st.session_state.auth_mode == "Login to your MemoBrain account" else 1,
            horizontal=True,
            key="auth_mode"
        )
    
    with col2:
        # Add demo mode button
        st.button("🧪 Try Demo", on_click=enter_demo_mode, help="Try MemoBrain without creating an account")

    username = st.text_input("Username", key="auth_username")
    password = st.text_input("Password", type="password", key="auth_password")

    col_btn1, col_btn2 = st.columns(2)
    
    with col_btn1:
        st.button(
            "🔓 Submit",
            on_click=attempt_auth,
            args=(st.session_state.auth_mode, username, password),
            use_container_width=True
        )
    
    with col_btn2:
        st.button(
            "🧪 Demo Mode",
            on_click=enter_demo_mode,
            use_container_width=True,
            help="Try MemoBrain without creating an account"
        )
    
    # Add some information about demo mode
    st.markdown("---")
    st.markdown("**🧪 Demo Mode**: Try MemoBrain instantly without registration. Your data will be available for 1 hour.")

def get_logged_in_user():
    return st.session_state.get("user_id")
