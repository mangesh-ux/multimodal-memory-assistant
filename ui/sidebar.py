
import streamlit as st
from streamlit_option_menu import option_menu


def render_sidebar(user_id):
    with st.sidebar:
        st.markdown("## 📁 MemoBrain Navigation")
        st.success(f"🔐 Logged in as: `{user_id}`")

        st.markdown("---")
        st.markdown("### 🧾 Main Menu")

        if "current_page" not in st.session_state:
            st.session_state.current_page = "📦 Memory Manager"

        # This CSS applies broadly, and then we'll use conditional styling
        # based on `is_selected` for the specific button.
        st.markdown(
            """
            <style>
            /* Base style for all Streamlit buttons in the sidebar (or where these buttons appear) */
            div.stButton > button {
                display: block; /* Make buttons take full width */
                width: 100%;
                text-align: left; /* Align text to the left */
                font-size: 1rem;
                padding: 0.6rem 1rem;
                margin: 0.3rem 0;
                border: none;
                border-radius: 0.5rem;
                cursor: pointer;
                transition: background-color 0.2s, color 0.2s, font-weight 0.2s;
                box-shadow: none; /* Remove default shadow */
            }

            /* Hover effect for ALL buttons */
            div.stButton > button:hover {
                background-color: rgba(100, 100, 100, 0.2); /* A subtle hover */
                color: var(--text-color); /* Ensure text color adjusts */
            }

            /* This targets the specific selected button using its data-testid */
            /* Streamlit's data-testid for a button with key "btn_LABEL" and type "secondary" */
            /* looks something like "stButton-secondary-btn_LABEL" */
            </style>
            """,
            unsafe_allow_html=True
        )

        def nav_button(label, icon):
            page_key = f"{icon} {label}" # e.g., "Home 🏠"
            is_selected = st.session_state.current_page == page_key

            # Conditional styling for the selected button
            button_style_css = ""
            if is_selected:
                button_style_css = f"""
                    <style>
                    /* Target the specific button by its key when it's selected */
                    div.stButton > button[data-testid*="stButton-secondary-btn_{label}"] {{
                        background-color: #F63366; /* Streamlit's default primary color */
                        color: white;
                        font-weight: 700;
                    }}
                    /* Override hover for selected button */
                    div.stButton > button[data-testid*="stButton-secondary-btn_{label}"]:hover {{
                        background-color: #e02f5c; /* Slightly darker pink on hover */
                        color: white;
                    }}
                    </style>
                """
                st.markdown(button_style_css, unsafe_allow_html=True) # Inject this specific style

            # Use st.button directly. Streamlit will re-run the app when this button is clicked.
            # We use type="secondary" because its default background is transparent/matching,
            # making it easier to control with our custom CSS.
            if st.button(f"{icon} {label}", key=f"btn_{label}", type="secondary"):
                st.session_state.current_page = page_key
                st.rerun() # Use st.rerun() to immediately update the page based on new state


        nav_button("Memory Manager", "📦")
        nav_button("My Files", "📂")
        nav_button("Ask MemoBrain", "💬")

