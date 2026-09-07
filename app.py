import streamlit as st

st.set_page_config(
    page_title="Change Helper",
    page_icon="◼",
    layout="wide",
    initial_sidebar_state="expanded",
)

from core.session import init_state
from core.styles import apply_styles
from core.ui import render_login, sidebar_nav
from tools.am_handover import page_am_handover
from tools.excel_splitter import page_excel_splitter
from tools.rox_domain_grouper import page_domain_grouper
from tools.weekly_tasks import page_weekly_tasks_helper


def run_change_helper():
    """Single application entry point.

    Keeping the whole UI behind one hidden Streamlit page prevents any stale
    pages/dashboard.py or pages/settings.py files in an old deployment from
    becoming visible in Streamlit's automatic navigation.
    """
    apply_styles()
    init_state()

    if not st.session_state.get("logged_in") or not st.session_state.get("current_user"):
        st.session_state.logged_in = False
        st.session_state.current_user = None
        st.session_state.jira_me = None
        render_login()

    page = sidebar_nav()

    if page == "Weekly Tasks Helper":
        page_weekly_tasks_helper()
    elif page == "AM Handover":
        page_am_handover()
    elif page == "ROX Domain Grouper":
        page_domain_grouper()
    elif page == "Excel Splitter":
        page_excel_splitter()


# st.navigation disables the legacy pages/ directory for this app. position="hidden"
# also prevents Streamlit from drawing a second navigation block next to our own sidebar.
if hasattr(st, "navigation") and hasattr(st, "Page"):
    navigation = st.navigation(
        [st.Page(run_change_helper, title="Change Helper", default=True)],
        position="hidden",
    )
    navigation.run()
else:
    # Compatibility fallback for older Streamlit versions. .streamlit/config.toml
    # also disables automatic sidebar page navigation before first render.
    run_change_helper()
