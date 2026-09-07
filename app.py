import streamlit as st

st.set_page_config(
    page_title="Change Helper",
    page_icon="🛠️",
    layout="wide",
    initial_sidebar_state="expanded",
)

from core.session import init_state
from core.styles import apply_styles
from core.ui import render_login, sidebar_nav
from pages.dashboard import page_dashboard
from pages.settings import page_settings
from tools.am_handover import page_am_handover
from tools.excel_splitter import page_excel_splitter
from tools.rox_domain_grouper import page_domain_grouper
from tools.weekly_tasks import page_weekly_tasks_helper


apply_styles()
init_state()

if not st.session_state.get("logged_in") or not st.session_state.get("current_user"):
    st.session_state.logged_in = False
    st.session_state.current_user = None
    st.session_state.jira_me = None
    render_login()

page = sidebar_nav()

if page == "Dashboard":
    page_dashboard()
elif page == "AM Handover":
    page_am_handover()
elif page == "Weekly Tasks Helper":
    page_weekly_tasks_helper()
elif page == "ROX Domain Grouper":
    page_domain_grouper()
elif page == "Excel Splitter":
    page_excel_splitter()
elif page == "Settings":
    page_settings()
