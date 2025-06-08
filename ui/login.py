from streamlit_login_auth_ui.widgets import login

def authenticate_user():
    __login_obj = login(
    auth_token="courier_auth_token_not_needed_for_local",
    company_name="MemoBrain",
    width=200,
    height=250,
    logout_button_name='Logout',
    hide_menu_bool=True,
    hide_footer_bool=True,
    lottie_url='https://assets2.lottiefiles.com/packages/lf20_jcikwtux.json',
    use_email=False, # 🔥 Skip email; use username only
    )
    return __login_obj.build()['username']

