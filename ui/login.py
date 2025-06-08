# login.py
import streamlit as st
from streamlit_login_auth_ui.widgets import __login__

def authenticate_user():
    __login_obj__ = __login__(
        auth_token="courier_auth_token",  # any string you want, just keep it same
        company_name="MemoBrain",
        width=200,
        height=250,
        logout_button_name='Logout',
        hide_menu_bool=True,
        hide_footer_bool=True,
        lottie_url="https://assets2.lottiefiles.com/packages/lf20_jcikwtux.json"  # optional animation
    )

    LOGGED_IN = __login_obj__.build_login_ui()

    if LOGGED_IN:
        user_details = __login_obj__.get_user_details()
        return user_details["username"]
    else:
        st.stop()
