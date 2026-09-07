import re

import streamlit as st

from core.config import (
    API_VERSION, AUTH_TYPE, JIRA_BASE_URL, MANUAL_FIELD_IDS, USER_PAYLOAD_TYPE,
)
from core.jira import get_field_map

def init_state():
    defaults = {
        "logged_in": False,
        "current_user": None,
        "jira_me": None,
        "zip_data": None,
        "zip_name": None,
        "split_ready": False,
    }
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value

def current_jira_context():
    current_user = st.session_state.current_user or {}
    jira_base_url = JIRA_BASE_URL
    api_version = API_VERSION
    auth_type = current_user.get("jira_auth_type", AUTH_TYPE)
    username = current_user.get("jira_username", "")
    token = current_user.get("jira_token", "")
    user_payload_type = current_user.get("user_payload_type", USER_PAYLOAD_TYPE)
    return jira_base_url, api_version, auth_type, username, token, user_payload_type

def require_jira_settings():
    jira_base_url, api_version, auth_type, username, token, _ = current_jira_context()
    token_text = (token or "").strip()

    if not jira_base_url:
        st.error("Jira Base URL is not configured in secrets.toml.")
        return False
    if not token_text or "PASTE_" in token_text:
        st.error("Jira credentials are not configured in .streamlit/secrets.toml. Password opens the app; token connects Jira. Obviously one password was too merciful.")
        return False
    if auth_type == "Basic" and not username:
        st.error("Jira username is not configured in .streamlit/secrets.toml.")
        return False
    if auth_type not in ["Basic", "Bearer"]:
        st.error('jira_auth_type must be either "Basic" or "Bearer".')
        return False
    return True

def get_cached_field_map():
    jira_base_url, api_version, auth_type, username, token, _ = current_jira_context()
    cache_key = f"field_map_{username}_{auth_type}"
    if cache_key not in st.session_state:
        st.session_state[cache_key] = get_field_map(jira_base_url, api_version, auth_type, username, token, MANUAL_FIELD_IDS)
    return st.session_state[cache_key]

def clear_handover_results():
    for key in [
        "handover_groups",
        "handover_jqls",
        "handover_search_errors",
        "loaded_projects",
        "loaded_current_person",
        "confirm_handover",
        "handover_synced_excluded_keys",
        "handover_editor_version",
    ]:
        st.session_state.pop(key, None)

    for key in list(st.session_state.keys()):
        if str(key).startswith("handover_editor_"):
            st.session_state.pop(key, None)
