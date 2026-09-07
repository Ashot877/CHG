from html import escape

import streamlit as st

from core.config import APP_TITLE, APP_SUBTITLE, APP_USERS, AUTH_TYPE, JIRA_BASE_URL, API_VERSION, VERIFY_JIRA_ON_LOGIN
from core.jira import jira_get_myself
from core.session import clear_handover_results


NAV_ITEMS = {
    "Weekly Tasks": "Weekly Tasks Helper",
    "AM Handover": "AM Handover",
    "ROX Domains": "ROX Domain Grouper",
    "Excel Splitter": "Excel Splitter",
}


def render_login():
    st.markdown(
        f"""
        <div class="login-shell">
          <div class="login-card">
            <div class="login-brand">Digitain · Change Management</div>
            <div class="login-title">{escape(APP_TITLE)}</div>
            <div class="login-subtitle">{escape(APP_SUBTITLE)}<br>Secure internal access with Jira verification.</div>
            <div class="login-rule"></div>
          </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    left, center, right = st.columns([1.15, 1, 1.15])
    with center:
        entered_password = st.text_input(
            "Password",
            type="password",
            label_visibility="collapsed",
            placeholder="Enter access password",
        )
        login_clicked = st.button("Enter workspace", type="primary", use_container_width=True)

        if not APP_USERS:
            st.warning("No users are configured in `.streamlit/secrets.toml`.")

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
                    with st.spinner("Verifying Jira access..."):
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


def render_hero(title, subtitle, pills=None, eyebrow="Change Management · Internal Workspace"):
    pills = pills or []
    pill_html = "".join([f'<span class="pill">{escape(str(pill))}</span>' for pill in pills])
    st.markdown(
        f"""
        <div class="hero">
            <div class="hero-eyebrow">{escape(eyebrow)}</div>
            <div class="hero-title">{escape(title)}</div>
            <div class="hero-subtitle">{escape(subtitle)}</div>
            <div class="pill-row">{pill_html}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def sidebar_nav():
    current_user = st.session_state.current_user or {}
    display_name = current_user.get("display_name") or current_user.get("jira_username") or "User"
    jira_name = display_name
    jira_connected = False
    if st.session_state.jira_me:
        me = st.session_state.jira_me
        jira_name = me.get("displayName") or me.get("name") or display_name
        jira_connected = True

    st.sidebar.markdown(
        """
        <div class="brand-lockup">
          <div class="brand-row">
            <div class="brand-mark">CH</div>
            <div>
              <div class="brand-title">CHANGE OPS</div>
              <div class="brand-subtitle">Digitain · Internal</div>
            </div>
          </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    status_text = "Jira connected" if jira_connected else "Workspace ready"
    st.sidebar.markdown(
        f"""
        <div class="user-chip">
          <div class="user-name">{escape(str(jira_name))}</div>
          <div class="user-meta"><span class="status-dot"></span>{escape(status_text)}</div>
        </div>
        <div class="nav-label">Tools</div>
        """,
        unsafe_allow_html=True,
    )

    selected_label = st.sidebar.radio(
        "Navigation",
        list(NAV_ITEMS.keys()),
        label_visibility="collapsed",
        key="main_navigation",
    )

    st.sidebar.divider()
    if st.sidebar.button("Log out", use_container_width=True):
        st.session_state.logged_in = False
        st.session_state.current_user = None
        st.session_state.jira_me = None
        clear_handover_results()
        st.rerun()

    st.sidebar.markdown(
        '<div class="sidebar-footer">CHANGE HELPER · Internal operations workspace<br>Jira writes remain behind preview and confirmation.</div>',
        unsafe_allow_html=True,
    )
    return NAV_ITEMS[selected_label]
