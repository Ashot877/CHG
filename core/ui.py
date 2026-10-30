from html import escape

import streamlit as st

from core.config import APP_TITLE, APP_SUBTITLE, APP_USERS, AUTH_TYPE, JIRA_BASE_URL, API_VERSION, VERIFY_JIRA_ON_LOGIN
from core.jira import jira_get_myself
from core.session import clear_handover_results
from core.themes import THEMES, get_active_theme, is_preview_allowed


NAV_ITEMS = {
    "Weekly Tasks": "Weekly Tasks Helper",
    "AM Handover": "AM Handover",
    "Comment Review": "Comment Review",
    "ROX Domains": "ROX Domain Grouper",
    "Excel Splitter": "Excel Splitter",
}


def render_login():
    left, center, right = st.columns([1.15, 1, 1.15])
    with center:
        with st.form("login_form", clear_on_submit=False, border=False):
            st.markdown(
                f"""
                <div class="login-header">
                    <div class="login-mark">CH</div>
                    <div class="login-eyebrow">Internal workspace</div>
                    <div class="login-title">{escape(APP_TITLE)}</div>
                    <div class="login-subtitle">{escape(APP_SUBTITLE)}</div>
                </div>
                """,
                unsafe_allow_html=True,
            )

            entered_password = st.text_input(
                "Access password",
                type="password",
                placeholder="Enter password",
                help="Your Jira access is verified after sign-in.",
            )
            login_clicked = st.form_submit_button(
                "Continue",
                type="primary",
                use_container_width=True,
            )
            st.markdown(
                '<div class="login-note">Jira access is checked securely after sign-in.</div>',
                unsafe_allow_html=True,
            )

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


def render_hero(title, subtitle, pills=None, eyebrow="Change Operations"):
    # One shared hero for every tool. Personalization is purely visual.
    theme = get_active_theme()
    is_personal = theme["id"] != "default"
    pills = list(pills or [])
    if is_personal:
        pills.insert(0, theme["badge"])
    pill_html = "".join(
        f'<span class="pill{(" personal-edition-pill" if is_personal and idx == 0 else "")}">{escape(str(pill))}</span>'
        for idx, pill in enumerate(pills)
    )
    stamp_html = (
        '<div class="personal-hero-stamp" aria-hidden="true">'
        f'<strong>{escape(theme["monogram"])}</strong><small>EDITION</small></div>'
        if is_personal else ""
    )
    st.markdown(
        f"""
        <div class="hero">
            <div class="hero-eyebrow">{escape(eyebrow)}</div>
            <div class="hero-title">{escape(title)}</div>
            <div class="hero-subtitle">{escape(subtitle)}</div>
            <div class="pill-row">{pill_html}</div>
            {stamp_html}
        </div>
        """,
        unsafe_allow_html=True,
    )


def sidebar_nav():
    current_user = st.session_state.current_user or {}
    theme = get_active_theme()
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
              <div class="brand-title">Change Helper</div>
              <div class="brand-subtitle">Change Management</div>
            </div>
          </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    status_text = "Jira connected" if jira_connected else "Workspace ready"
    welcome_html = ""
    if theme["id"] != "default":
        welcome_html = f"""
        <div class="personal-welcome">
            <div class="personal-welcome-kicker">✦ {escape(theme['badge'])}</div>
            <div class="personal-welcome-title">Welcome back, {escape(str(display_name))}!</div>
            <div class="personal-welcome-note">{escape(theme['note'])}</div>
            <div class="personal-stripes" aria-hidden="true"><i></i><i></i><i></i><i></i><i></i></div>
        </div>
        """
    st.sidebar.markdown(
        f"""
        <div class="user-chip">
          <div class="user-name">{escape(str(jira_name))}</div>
          <div class="user-meta"><span class="status-dot"></span>{escape(status_text)}</div>
        </div>
        {welcome_html}
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

    # Available only for explicitly allowlisted testers, not regular employees.
    # This never changes their Jira identity or credentials.
    if is_preview_allowed(current_user):
        st.sidebar.selectbox(
            "Theme preview · visual only",
            options=["account", *THEMES.keys()],
            format_func=lambda key: "My assigned theme" if key == "account" else THEMES[key]["name"],
            key="theme_preview",
            help="Try another appearance without switching accounts. Disable in production Secrets.",
        )

    st.sidebar.markdown('<div class="logout-separator"></div>', unsafe_allow_html=True)
    if st.sidebar.button("Log out", use_container_width=True, key="logout_button"):
        st.session_state.logged_in = False
        st.session_state.current_user = None
        st.session_state.jira_me = None
        st.session_state.pop("theme_preview", None)
        clear_handover_results()
        st.rerun()

    st.sidebar.markdown(
        '<div class="sidebar-footer">Change Helper<br><span>Safe updates with preview and confirmation.</span></div>',
        unsafe_allow_html=True,
    )
    return NAV_ITEMS[selected_label]
