import streamlit as st

from core.config import APP_TITLE, APP_SUBTITLE, APP_USERS, AUTH_TYPE, JIRA_BASE_URL, API_VERSION, VERIFY_JIRA_ON_LOGIN
from core.jira import jira_get_myself
from core.session import clear_handover_results

def render_login():
    st.markdown(
        f"""
        <div class="login-shell">
          <div class="login-card">
            <div class="login-icon">🛠️</div>
            <div class="login-title">{APP_TITLE}</div>
            <div class="login-subtitle">{APP_SUBTITLE}<br>Enter password. If Jira is configured, the app will verify API access immediately.</div>
          </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # Streamlit cannot place native inputs inside the HTML card, so this is intentionally below it.
    login_col1, login_col2, login_col3 = st.columns([1.15, 1, 1.15])
    with login_col2:
        entered_password = st.text_input("Password", type="password", label_visibility="collapsed", placeholder="Password")
        login_clicked = st.button("Open Change Helper", type="primary", use_container_width=True)

        if not APP_USERS:
            st.warning("No users found. Create `.streamlit/secrets.toml` first. Humanity has once again hidden the keys under the doormat.")

        if login_clicked:
            entered_password_clean = (entered_password or "").strip()
            user_config = APP_USERS.get(entered_password_clean)

            if not user_config:
                st.session_state.logged_in = False
                st.session_state.current_user = None
                st.session_state.jira_me = None
                st.error("Wrong password.")
                st.stop()

            token = (user_config.get("jira_token") or "").strip()
            auth_type = user_config.get("jira_auth_type", AUTH_TYPE)
            username = user_config.get("jira_username", "")

            if VERIFY_JIRA_ON_LOGIN and token and "PASTE_" not in token:
                try:
                    with st.spinner("Checking Jira API access..."):
                        me = jira_get_myself(JIRA_BASE_URL, API_VERSION, auth_type, username, token)
                    st.session_state.jira_me = me
                except Exception as e:
                    st.session_state.logged_in = False
                    st.session_state.current_user = None
                    st.session_state.jira_me = None
                    st.error("Password is correct, but Jira API connection failed.")
                    st.code(str(e))
                    st.stop()

            st.session_state.logged_in = True
            st.session_state.current_user = user_config
            st.rerun()

    st.stop()

def render_hero(title, subtitle, pills=None):
    pills = pills or []
    pill_html = "".join([f'<span class="pill">{pill}</span>' for pill in pills])
    st.markdown(
        f"""
        <div class="hero">
            <div class="hero-title">{title}</div>
            <div class="hero-subtitle">{subtitle}</div>
            <div class="pill-row">{pill_html}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def sidebar_nav():
    current_user = st.session_state.current_user or {}
    display_name = current_user.get("display_name") or current_user.get("jira_username") or "User"

    st.sidebar.markdown(f"### 🛠️ {APP_TITLE}")
    st.sidebar.caption(f"Logged in as **{display_name}**")
    if st.session_state.jira_me:
        me = st.session_state.jira_me
        st.sidebar.caption(f"Jira: **{me.get('displayName') or me.get('name') or display_name}**")

    page = st.sidebar.radio(
        "Navigation",
        ["Dashboard", "AM Handover", "Weekly Tasks Helper", "ROX Domain Grouper", "Excel Splitter", "Settings"],
        label_visibility="collapsed",
    )

    st.sidebar.divider()
    if st.sidebar.button("Logout", use_container_width=True):
        st.session_state.logged_in = False
        st.session_state.current_user = None
        st.session_state.jira_me = None
        clear_handover_results()
        st.rerun()

    st.sidebar.markdown(
        '<div class="footer-note">Internal workspace · Jira writes always stay behind an explicit preview/confirmation step.</div>',
        unsafe_allow_html=True,
    )
    return page
