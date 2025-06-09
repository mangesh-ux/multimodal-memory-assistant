
import streamlit as st
from streamlit_option_menu import option_menu


def render_sidebar(user_id):
    with st.sidebar:
        st.markdown("## 📁 MemoBrain Navigation")
        st.success(f"🔐 Logged in as: `{user_id}`")

        st.markdown("---")
        st.markdown("### 🧭 Navigate")

        nav_styles = """
            <style>
            .sidebar-nav .nav-button {
                display: block;
                width: 100%;
                padding: 0.75rem 1rem;
                margin-bottom: 0.5rem;
                border: none;
                border-radius: 0.5rem;
                background-color: #1c1c1c;
                color: #fff;
                font-size: 1rem;
                text-align: left;
                cursor: pointer;
                transition: background 0.3s;
            }

            .sidebar-nav .nav-button:hover {
                background-color: #333;
            }

            .sidebar-nav .nav-selected {
                background-color: #f63366;
                color: #fff;
                font-weight: bold;
            }
            </style>
        """
        st.markdown(nav_styles, unsafe_allow_html=True)

        def nav_button(label, icon):
            nav_key = f"{icon} {label}"
            if st.session_state.get("current_page", "📦 Memory Manager") == nav_key:
                button_html = f'<button class="nav-button nav-selected">{icon} {label}</button>'
            else:
                button_html = f'<button class="nav-button" onclick="window.location.reload();">{icon} {label}</button>'
            st.markdown(button_html, unsafe_allow_html=True)
            if st.button(f"{icon} {label}", key=f"{label}_btn"):
                st.session_state.current_page = nav_key

        st.markdown('<div class="sidebar-nav">', unsafe_allow_html=True)
        nav_button("Memory Manager", "📦")
        nav_button("My Files", "📂")
        nav_button("Ask MemoBrain", "💬")
        st.markdown('</div>', unsafe_allow_html=True)
