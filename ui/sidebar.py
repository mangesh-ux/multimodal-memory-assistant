
import streamlit as st
from streamlit_option_menu import option_menu


def render_sidebar(user_id):
    with st.sidebar:
        st.markdown("## 📁 MemoBrain Navigation")
        st.success(f"🔐 Logged in as: `{user_id}`")

        st.markdown("---")
        st.markdown("### 🧭 📂 Main Menu")

        if "current_page" not in st.session_state:
            st.session_state.current_page = "📦 Memory Manager"

        def nav_button(label, icon):
            page_key = f"{icon} {label}"
            is_selected = st.session_state.current_page == page_key
            style = f"""
                <style>
                    .nav-button {{
                        display: block;
                        width: 100%;
                        background-color: {'#F63366' if is_selected else '#262730'};
                        color: {'white' if is_selected else '#ffffffaa'};
                        font-weight: {'700' if is_selected else '500'};
                        padding: 0.6rem 1rem;
                        margin: 0.3rem 0;
                        border: none;
                        border-radius: 0.5rem;
                        text-align: left;
                        cursor: pointer;
                    }}
                    .nav-button:hover {{
                        background-color: #444;
                    }}
                </style>
                <button class="nav-button" onclick="window.location.reload();">{icon} {label}</button>
            """
            st.markdown(style, unsafe_allow_html=True)
            if st.button(f"{icon} {label}", key=f"btn_{label}"):
                st.session_state.current_page = page_key

        nav_button("Memory Manager", "📦")
        nav_button("My Files", "📂")
        nav_button("Ask MemoBrain", "💬")

