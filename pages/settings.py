import streamlit as st

from core.config import MANUAL_FIELD_IDS
from core.jira import jira_get_myself
from core.session import current_jira_context, require_jira_settings
from core.ui import render_hero

def page_settings():
    render_hero("Settings", "Read-only view of current app configuration. Real secrets stay hidden, as nature intended.", ["Secrets", "Jira", "Users"])

    st.markdown('<div class="section-card">', unsafe_allow_html=True)
    st.subheader("Jira connection")
    jira_base_url, api_version, auth_type, username, token, user_payload_type = current_jira_context()

    s1, s2, s3 = st.columns(3)
    s1.text_input("Jira base URL", value=jira_base_url, disabled=True)
    s2.text_input("API version", value=api_version, disabled=True)
    s3.text_input("User payload type", value=user_payload_type, disabled=True)

    s4, s5 = st.columns(2)
    s4.text_input("Auth type", value=auth_type, disabled=True)
    s5.text_input("Current Jira username", value=username, disabled=True)

    if st.button("Check Jira connection", type="primary"):
        if require_jira_settings():
            try:
                me = jira_get_myself(jira_base_url, api_version, auth_type, username, token)
                st.session_state.jira_me = me
                st.success(f"Connected as {me.get('displayName') or me.get('name') or username}")
            except Exception as e:
                st.error("Jira connection failed")
                st.code(str(e))
    st.markdown('</div>', unsafe_allow_html=True)

    st.markdown('<div class="section-card">', unsafe_allow_html=True)
    st.subheader("Manual field IDs")
    f1, f2 = st.columns(2)
    f1.text_input("Internal Reporter", value=MANUAL_FIELD_IDS.get("Internal Reporter") or "Auto-detect", disabled=True)
    f2.text_input("Waiting information from", value=MANUAL_FIELD_IDS.get("Waiting information from") or "Auto-detect", disabled=True)
    st.caption("If field IDs are empty, the app will call Jira `/field` and try to detect them by name.")
    st.markdown('</div>', unsafe_allow_html=True)
